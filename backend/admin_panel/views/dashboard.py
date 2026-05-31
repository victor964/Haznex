from datetime import timedelta

from django.db.models import Count, Max
from django.utils import timezone
from django.views.generic import TemplateView

from admin_panel.mixins import HaznexAdminRequiredMixin
from orders.models import Order, OrderStatusUpdate
from store.choices import ORDER_STATUS_FLOW, TERMINAL_ORDER_STATUSES, OrderStatus
from store.models import Product


class DashboardView(HaznexAdminRequiredMixin, TemplateView):
    template_name = "admin_panel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_products"] = Product.objects.count()
        context["active_products"] = Product.objects.filter(is_active=True).count()
        context["total_orders"] = Order.objects.count()
        context["orders_completed"] = Order.objects.filter(
            status=OrderStatus.COMPLETED
        ).count()

        status_counts = (
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        status_labels = dict(OrderStatus.choices)
        context["orders_by_status"] = [
            {
                "status": row["status"],
                "label": status_labels.get(row["status"], row["status"]),
                "count": row["count"],
            }
            for row in status_counts
        ]

        context["recent_action_orders"] = (
            Order.objects.select_related("product", "client")
            .exclude(
                status__in=TERMINAL_ORDER_STATUSES,
            )
            .order_by("-created_at")[:5]
        )

        since = timezone.now() - timedelta(hours=24)
        context["pending_payment_count"] = Order.objects.filter(
            status=OrderStatus.PAYMENT_PENDING,
            created_at__gte=since,
        ).count()

        active_orders = (
            Order.objects.exclude(status__in=TERMINAL_ORDER_STATUSES)
            .select_related("product", "client")
            .annotate(last_status_update_at=Max("status_updates__created_at"))
            .order_by("-created_at")
        )
        now = timezone.now()
        grouped = {}
        for order in active_orders:
            grouped.setdefault(order.status, []).append(order)

        action_groups = []
        for status in ORDER_STATUS_FLOW:
            orders = grouped.get(status)
            if not orders:
                continue
            for order in orders:
                last_at = order.last_status_update_at or order.created_at
                order.days_since_update = (now.date() - last_at.date()).days
            action_groups.append(
                {
                    "status": status,
                    "label": status_labels.get(status, status),
                    "count": len(orders),
                    "orders": orders,
                    "card_class": _action_card_class(status),
                }
            )
        context["orders_needing_action"] = action_groups

        context["recent_activity"] = (
            OrderStatusUpdate.objects.select_related("order", "updated_by")
            .order_by("-created_at")[:10]
        )

        return context


def _action_card_class(status):
    if status == OrderStatus.PAYMENT_PENDING:
        return "haznex-action-urgent"
    if status in (OrderStatus.SHIPPED_FROM_UK, OrderStatus.IN_TRANSIT):
        return "haznex-action-shipping"
    return "haznex-action-neutral"
