from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin


class OrderOwnerMixin(LoginRequiredMixin):
    """Ensure the order belongs to the logged-in client."""

    login_url = "accounts:login"

    def get_order(self):
        order_number = self.kwargs.get("order_number")
        order = self.get_queryset().filter(order_number=order_number).first()
        if order is None:
            raise Http404("Order not found.")
        if order.client_id != self.request.user.id:
            raise Http404("Order not found.")
        return order

    def get_object(self):
        return self.get_order()
