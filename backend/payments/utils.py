import re

from django.http import Http404
from django.shortcuts import get_object_or_404

from orders.models import Order

_KENYA_MOBILE_RE = re.compile(r"^2547\d{8}$")


def normalize_mpesa_phone(raw):
    """
    Accept 07XXXXXXXX, 2547XXXXXXXX, or +2547XXXXXXXX.
    Return 2547XXXXXXXX or None if invalid.
    """
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw.strip())
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    elif digits.startswith("254"):
        pass
    elif digits.startswith("7") and len(digits) == 9:
        digits = "254" + digits
    if _KENYA_MOBILE_RE.match(digits):
        return digits
    return None


def get_client_order(user, order_number):
    """Load order for the authenticated client or raise Http404."""
    order = get_object_or_404(
        Order.objects.select_related("product", "payment"),
        order_number=order_number,
    )
    if order.client_id != user.id:
        raise Http404
    return order
