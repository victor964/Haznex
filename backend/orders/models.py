from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Max

from store.choices import ORDER_STATUS_FLOW, TERMINAL_ORDER_STATUSES, OrderStatus
from store.models import MONEY_VALIDATORS, Product, ShippingOption

QUANTITY_VALIDATORS = [MinValueValidator(1)]


class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    shipping_method = models.ForeignKey(
        ShippingOption,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    quantity = models.PositiveIntegerField(default=1, validators=QUANTITY_VALIDATORS)
    delivery_address = models.TextField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="KES — product unit price at order time",
    )
    shipping_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        validators=MONEY_VALIDATORS,
        help_text="KES",
    )
    local_delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        validators=MONEY_VALIDATORS,
        help_text="KES — local delivery added separately",
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="KES — immutable order total snapshot",
    )
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PAYMENT_PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["client"]),
            models.Index(fields=["order_number"]),
        ]

    def __str__(self):
        return self.order_number

    def calculate_total_price(self):
        return (
            self.unit_price * self.quantity
            + self.shipping_fee
            + self.local_delivery_fee
        )

    def clean(self):
        super().clean()
        expected_total = self.calculate_total_price()
        if self.total_price != expected_total:
            raise ValidationError(
                {
                    "total_price": (
                        f"Must equal (unit_price × quantity) + shipping_fee + "
                        f"local_delivery_fee ({expected_total} KES)."
                    )
                }
            )

    @classmethod
    def _generate_order_number(cls):
        today = date.today().strftime("%Y%m%d")
        prefix = f"VH-{today}-"
        last = (
            cls.objects.filter(order_number__startswith=prefix)
            .aggregate(max_num=Max("order_number"))
            .get("max_num")
        )
        if last:
            seq = int(last.rsplit("-", 1)[-1]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)
        if is_new:
            OrderStatusUpdate.objects.create(
                order=self,
                status=OrderStatus.PAYMENT_PENDING,
                note="Order placed",
                updated_by=None,
            )


class OrderStatusUpdate(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_updates",
    )
    status = models.CharField(max_length=30, choices=OrderStatus.choices)
    note = models.TextField()
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="order_status_updates",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.order.order_number} → {self.get_status_display()} at {self.created_at}"

    def clean(self):
        super().clean()
        if self.updated_by_id:
            profile = getattr(self.updated_by, "profile", None)
            if profile is None or not profile.is_admin:
                raise ValidationError(
                    {"updated_by": "Only VH Bridge admins can update order status."}
                )

    @staticmethod
    def get_next_status(current_status):
        if current_status in TERMINAL_ORDER_STATUSES:
            return None
        try:
            idx = ORDER_STATUS_FLOW.index(current_status)
        except ValueError:
            return None
        if idx + 1 < len(ORDER_STATUS_FLOW):
            return ORDER_STATUS_FLOW[idx + 1]
        return None

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.order.status != self.status:
                self.order.status = self.status
                self.order.save(update_fields=["status", "updated_at"])
