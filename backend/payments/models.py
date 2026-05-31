from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from store.models import MONEY_VALIDATORS


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Payment(models.Model):
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    phone_number = models.CharField(
        max_length=15,
        help_text="M-Pesa number in format 2547XXXXXXXX",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="KES amount charged",
    )
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    stk_push_initiated = models.BooleanField(default=False)
    manually_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} — {self.get_status_display()}"
