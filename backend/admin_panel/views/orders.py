from django.contrib import messages
from django.db import transaction
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, View

from admin_panel.forms.orders import OrderStatusUpdateForm
from admin_panel.mixins import HaznexAdminRequiredMixin
from orders.models import Order, OrderStatusUpdate
from payments.models import Payment, PaymentStatus
from store.choices import TERMINAL_ORDER_STATUSES, OrderStatus


class OrderListView(HaznexAdminRequiredMixin, ListView):
    model = Order
    template_name = "admin_panel/orders/list.html"
    context_object_name = "orders"
    paginate_by = 25

    ACTIVE_STATUSES = [
        OrderStatus.PAYMENT_CONFIRMED,
        OrderStatus.SOURCING_ITEM,
        OrderStatus.SHIPPED_FROM_UK,
        OrderStatus.IN_TRANSIT,
        OrderStatus.ARRIVED_IN_KENYA,
        OrderStatus.OUT_FOR_DELIVERY,
    ]

    def get_queryset(self):
        qs = (
            Order.objects.select_related("product", "client", "shipping_method")
            .annotate(last_status_update_at=Max("status_updates__created_at"))
            .order_by("-created_at")
        )
        quick_filter = self.request.GET.get("filter", "")
        if quick_filter == "needs_payment":
            qs = qs.filter(status=OrderStatus.PAYMENT_PENDING)
        elif quick_filter == "active":
            qs = qs.filter(status__in=self.ACTIVE_STATUSES)
        elif quick_filter == "completed":
            qs = qs.filter(status=OrderStatus.COMPLETED)
        elif quick_filter == "cancelled":
            qs = qs.filter(status=OrderStatus.CANCELLED)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(order_number__icontains=q)
                | Q(product__name__icontains=q)
                | Q(client__username__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_status"] = self.request.GET.get("status", "")
        context["search_q"] = self.request.GET.get("q", "")
        context["quick_filter"] = self.request.GET.get("filter", "")
        context["status_choices"] = OrderStatus.choices

        now = timezone.now().date()
        order_rows = []
        for order in context["orders"]:
            last_at = order.last_status_update_at or order.created_at
            days_since_update = (now - last_at.date()).days
            order_rows.append(
                {
                    "order": order,
                    "days_active": (now - order.created_at.date()).days,
                    "days_since_update": days_since_update,
                    "is_stale": days_since_update > 3
                    and order.status not in TERMINAL_ORDER_STATUSES,
                }
            )
        context["order_rows"] = order_rows
        return context

class OrderDetailView(HaznexAdminRequiredMixin, View):
    template_name = "admin_panel/orders/detail.html"

    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related(
                "product", "client", "shipping_method", "payment"
            ),
            pk=pk,
        )
        status_updates = order.status_updates.select_related("updated_by").all()
        status_form = OrderStatusUpdateForm(order=order)
        if order.status in TERMINAL_ORDER_STATUSES:
            status_form = None
        return render(
            request,
            self.template_name,
            {
                "order": order,
                "status_updates": status_updates,
                "status_form": status_form,
                "payment": getattr(order, "payment", None),
            },
        )

    def post(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related("payment"),
            pk=pk,
        )
        if order.status in TERMINAL_ORDER_STATUSES:
            messages.error(request, "This order can no longer be updated.")
            return redirect("admin_panel:order_detail", pk=pk)

        form = OrderStatusUpdateForm(request.POST, order=order)
        if form.is_valid():
            OrderStatusUpdate.objects.create(
                order=order,
                status=form.cleaned_data["status"],
                note=form.cleaned_data["note"],
                updated_by=request.user,
            )
            status_label = OrderStatus(form.cleaned_data["status"]).label
            messages.success(
                request,
                f"Order {order.order_number} updated to {status_label}.",
            )
            return redirect("admin_panel:order_detail", pk=pk)
        status_updates = order.status_updates.select_related("updated_by").all()
        return render(
            request,
            self.template_name,
            {
                "order": order,
                "status_updates": status_updates,
                "status_form": form,
                "payment": getattr(order, "payment", None),
            },
        )


class ConfirmPaymentView(HaznexAdminRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related("payment"),
            pk=pk,
        )
        payment = getattr(order, "payment", None)
        if not payment:
            messages.error(request, "No payment record found for this order.")
            return redirect("admin_panel:order_detail", pk=pk)
        if payment.status == PaymentStatus.COMPLETED:
            messages.info(request, "Payment is already confirmed.")
            return redirect("admin_panel:order_detail", pk=pk)

        payment.status = PaymentStatus.COMPLETED
        payment.manually_confirmed = True
        payment.save(update_fields=["status", "manually_confirmed", "updated_at"])

        OrderStatusUpdate.objects.create(
            order=order,
            status=OrderStatus.PAYMENT_CONFIRMED,
            note=f"Payment manually confirmed by admin {request.user.username}",
            updated_by=request.user,
        )

        messages.success(request, "Payment confirmed. Order is now active.")
        return redirect("admin_panel:order_detail", pk=pk)


class CancelOrderView(HaznexAdminRequiredMixin, View):
    template_name = "admin_panel/orders/cancel_confirm.html"

    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related("product", "client"),
            pk=pk,
        )
        if order.status in TERMINAL_ORDER_STATUSES:
            messages.error(request, "This order cannot be cancelled.")
            return redirect("admin_panel:order_detail", pk=pk)
        return render(request, self.template_name, {"order": order})

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status in TERMINAL_ORDER_STATUSES:
            messages.error(request, "This order cannot be cancelled.")
            return redirect("admin_panel:order_detail", pk=pk)

        with transaction.atomic():
            OrderStatusUpdate.objects.create(
                order=order,
                status=OrderStatus.CANCELLED,
                note=f"Order cancelled by admin {request.user.username}",
                updated_by=request.user,
            )

        messages.success(
            request,
            f"Order {order.order_number} has been cancelled.",
        )
        return redirect("admin_panel:order_detail", pk=pk)
