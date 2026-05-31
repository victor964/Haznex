import json

from django.contrib import messages
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from accounts.mixins import ClientRequiredMixin
from store.choices import ORDER_STATUS_FLOW, OrderStatus
from store.models import Product, ShippingOption

from .forms import OrderPlacementForm
from .models import Order
from .services.order_placement import calculate_shipping_fee, create_client_order


class OrderPlacementView(ClientRequiredMixin, FormView):
    template_name = "orders/place_order.html"
    form_class = OrderPlacementForm

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product.objects.filter(is_active=True, price_breakdown__isnull=False)
            .select_related("price_breakdown")
            .prefetch_related("images"),
            slug=kwargs["slug"],
        )
        if not self.product.weight_kg or not self.product.final_client_price:
            messages.error(request, "This product cannot be ordered at this time.")
            return redirect("store:product_detail", slug=self.product.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["product"] = self.product
        return kwargs

    def get_initial(self):
        profile = self.request.user.profile
        return {"delivery_address": profile.delivery_address}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.product
        options_with_cost = []
        shipping_costs = {}
        for option in ShippingOption.objects.filter(is_active=True):
            cost = calculate_shipping_fee(option, product.weight_kg)
            shipping_costs[str(option.pk)] = float(cost) if cost else None
            options_with_cost.append({"option": option, "cost": cost})

        context["product"] = product
        context["options_with_cost"] = options_with_cost
        context["unit_price"] = float(product.final_client_price)
        context["shipping_costs_json"] = json.dumps(shipping_costs)
        return context

    def form_valid(self, form):
        try:
            order = create_client_order(
                product=self.product,
                client=self.request.user,
                shipping_method=form.cleaned_data["shipping_method"],
                delivery_address=form.cleaned_data["delivery_address"],
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Order {order.order_number} placed successfully. Please complete payment.",
        )
        return redirect("payments:pay", order_number=order.order_number)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ClientOrderListView(ClientRequiredMixin, ListView):
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return (
            Order.objects.filter(client=self.request.user)
            .select_related("product", "shipping_method")
            .prefetch_related("product__images")
            .annotate(last_status_update_at=Max("status_updates__created_at"))
            .order_by("-created_at")
        )


class OrderTrackingView(ClientRequiredMixin, DetailView):
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"

    def get_queryset(self):
        return (
            Order.objects.filter(client=self.request.user)
            .select_related("product", "shipping_method", "client")
            .prefetch_related("product__images", "status_updates")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        updates_by_status = {
            update.status: update for update in order.status_updates.all()
        }

        flow = list(ORDER_STATUS_FLOW)
        if order.status == OrderStatus.CANCELLED:
            flow = flow + [OrderStatus.CANCELLED]

        current_index = flow.index(order.status) if order.status in flow else -1
        timeline_steps = []
        for index, status in enumerate(flow):
            update = updates_by_status.get(status)
            if order.status == OrderStatus.CANCELLED and status != OrderStatus.CANCELLED:
                state = "cancelled" if index > current_index else (
                    "completed" if update else "pending"
                )
            elif index < current_index:
                state = "completed"
            elif index == current_index:
                state = "current"
            else:
                state = "pending"

            timeline_steps.append(
                {
                    "status": status,
                    "label": dict(OrderStatus.choices).get(status, status),
                    "state": state,
                    "note": update.note if update else "",
                    "timestamp": update.created_at if update else None,
                }
            )

        context["timeline_steps"] = timeline_steps
        context["is_payment_pending"] = order.status == OrderStatus.PAYMENT_PENDING
        context["is_cancelled"] = order.status == OrderStatus.CANCELLED
        cancelled_update = updates_by_status.get(OrderStatus.CANCELLED)
        context["cancellation_note"] = (
            cancelled_update.note if cancelled_update else ""
        )
        context["estimated_delivery_days"] = (
            order.shipping_method.estimated_delivery_days
        )
        return context
