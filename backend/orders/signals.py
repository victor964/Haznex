from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.email_notifications import send_order_status_email
from orders.models import OrderStatusUpdate


@receiver(post_save, sender=OrderStatusUpdate)
def notify_client_on_status_update(sender, instance, created, **kwargs):
    if not created:
        return
    send_order_status_email(instance.order, instance)
