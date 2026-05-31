from store.choices import OrderStatus
from orders.models import OrderStatusUpdate


def get_allowed_next_statuses(current_status):
    """Return list of (value, label) for valid next statuses."""
    allowed = []
    nxt = OrderStatusUpdate.get_next_status(current_status)
    if nxt:
        allowed.append((nxt, OrderStatus(nxt).label))
    if current_status in (OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_CONFIRMED):
        cancel = OrderStatus.CANCELLED
        if cancel not in [a[0] for a in allowed]:
            allowed.append((cancel, OrderStatus.CANCELLED.label))
    return allowed
