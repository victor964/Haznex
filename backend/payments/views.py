import json
import logging

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from accounts.mixins import ClientRequiredMixin
from orders.models import OrderStatusUpdate
from store.choices import OrderStatus

from .daraja import DarajaAPI
from .models import Payment, PaymentStatus
from .utils import get_client_order, normalize_mpesa_phone

logger = logging.getLogger("payments")


class PaymentPageView(ClientRequiredMixin, TemplateView):
    template_name = "payments/pay.html"

    def get_order(self):
        return get_client_order(self.request.user, self.kwargs["order_number"])

    def get(self, request, *args, **kwargs):
        order = self.get_order()
        payment = getattr(order, "payment", None)
        if payment and payment.status == PaymentStatus.COMPLETED:
            return redirect("payments:status", order_number=order.order_number)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_order()
        context["order"] = order
        context["product_name"] = order.product.name
        context["stk_enabled"] = settings.MPESA_STK_ENABLED
        context["payment"] = getattr(order, "payment", None)
        return context


class InitiateStkPushView(ClientRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, order_number):
        order = get_client_order(request.user, order_number)
        phone_raw = request.POST.get("phone_number", "")
        phone = normalize_mpesa_phone(phone_raw)
        if not phone:
            return JsonResponse(
                {"success": False, "error": "Invalid phone number"},
                status=400,
            )

        if not settings.MPESA_STK_ENABLED:
            return JsonResponse({"success": False, "reason": "stk_disabled"})

        api = DarajaAPI()
        result = api.stk_push(phone, order.total_price, order.order_number)

        if result.get("success") is False:
            return JsonResponse(
                {
                    "success": False,
                    "error": result.get(
                        "error",
                        "Could not initiate payment. Please try the manual confirmation.",
                    ),
                }
            )

        checkout_id = result.get("CheckoutRequestID", "")
        Payment.objects.update_or_create(
            order=order,
            defaults={
                "phone_number": phone,
                "amount": order.total_price,
                "mpesa_checkout_request_id": checkout_id,
                "stk_push_initiated": True,
                "status": PaymentStatus.PENDING,
            },
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Check your phone for the M-Pesa prompt",
            }
        )


class ManualPaymentConfirmView(ClientRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, order_number):
        order = get_client_order(request.user, order_number)
        phone_raw = request.POST.get("phone_number", "")
        phone = normalize_mpesa_phone(phone_raw)
        if not phone:
            messages.error(request, "Please enter a valid M-Pesa phone number.")
            return redirect("payments:pay", order_number=order_number)

        Payment.objects.update_or_create(
            order=order,
            defaults={
                "phone_number": phone,
                "amount": order.total_price,
                "manually_confirmed": True,
                "status": PaymentStatus.PENDING,
            },
        )

        OrderStatusUpdate.objects.create(
            order=order,
            status=OrderStatus.PAYMENT_PENDING,
            note=(
                f"Client has indicated payment was made. Awaiting admin verification. "
                f"Phone: {phone}"
            ),
            updated_by=None,
        )

        messages.success(
            request,
            "Thank you. We have received your payment notification. "
            "An admin will verify and confirm your order shortly. "
            "You can track your order status here.",
        )
        return redirect("orders:order_detail", order_number=order.order_number)


@method_decorator(csrf_exempt, name="dispatch")
class MpesaCallbackView(View):
    """Safaricom Daraja STK callback — always HTTP 200, never 500."""

    http_method_names = ["post"]

    def post(self, request):
        try:
            if request.body:
                data = json.loads(request.body)
            else:
                data = {}
            logger.info("M-Pesa callback received: %s", data)

            parsed = DarajaAPI.parse_callback(data)
            checkout_id = parsed.get("checkout_request_id")
            if not checkout_id:
                return self._accepted()

            try:
                payment = Payment.objects.select_related("order").get(
                    mpesa_checkout_request_id=checkout_id
                )
            except Payment.DoesNotExist:
                logger.warning(
                    "M-Pesa callback: no payment for CheckoutRequestID=%s",
                    checkout_id,
                )
                return self._accepted()

            result_code = parsed.get("result_code")
            if result_code == 0:
                if payment.status != PaymentStatus.COMPLETED:
                    receipt = parsed.get("mpesa_receipt_number", "")
                    payment.status = PaymentStatus.COMPLETED
                    payment.mpesa_receipt_number = receipt
                    payment.save(
                        update_fields=[
                            "status",
                            "mpesa_receipt_number",
                            "updated_at",
                        ]
                    )
                    OrderStatusUpdate.objects.create(
                        order=payment.order,
                        status=OrderStatus.PAYMENT_CONFIRMED,
                        note=f"Payment confirmed via M-Pesa. Receipt: {receipt}",
                        updated_by=None,
                    )
            else:
                payment.status = PaymentStatus.FAILED
                payment.save(update_fields=["status", "updated_at"])
                logger.info(
                    "M-Pesa payment failed for %s: %s",
                    checkout_id,
                    parsed.get("result_desc"),
                )

        except Exception:
            logger.exception("M-Pesa callback processing error")

        return self._accepted()

    @staticmethod
    def _accepted():
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


class PaymentStatusView(ClientRequiredMixin, TemplateView):
    template_name = "payments/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = get_client_order(self.request.user, self.kwargs["order_number"])
        context["order"] = order
        context["payment"] = getattr(order, "payment", None)
        return context
