from django import template

from store.choices import OrderStatus

register = template.Library()

STATUS_BADGE_CLASSES = {
    OrderStatus.PAYMENT_PENDING: "status-payment-pending",
    OrderStatus.PAYMENT_CONFIRMED: "status-payment-confirmed",
    OrderStatus.SOURCING_ITEM: "status-sourcing",
    OrderStatus.SHIPPED_FROM_UK: "status-shipped-uk",
    OrderStatus.IN_TRANSIT: "status-in-transit",
    OrderStatus.ARRIVED_IN_KENYA: "status-arrived-kenya",
    OrderStatus.OUT_FOR_DELIVERY: "status-out-for-delivery",
    OrderStatus.COMPLETED: "status-completed",
    OrderStatus.CANCELLED: "status-cancelled",
}


@register.filter
def order_status_badge_class(status):
    return STATUS_BADGE_CLASSES.get(status, "status-progress")


@register.filter
def admin_order_status_badge_class(status):
    """Admin panel uses the same colour mapping with haznex- prefix."""
    base = STATUS_BADGE_CLASSES.get(status, "status-progress")
    return f"haznex-{base}"
