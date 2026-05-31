from django.db import models


class ProductCondition(models.TextChoices):
    NEW = "new", "New"
    USED = "used", "Used"
    REFURBISHED = "refurbished", "Refurbished"


class SourceType(models.TextChoices):
    FACEBOOK_MARKETPLACE = "facebook_marketplace", "Facebook Marketplace"
    LOCAL = "local", "Local"


class OrderStatus(models.TextChoices):
    PAYMENT_PENDING = "payment_pending", "Payment Pending"
    PAYMENT_CONFIRMED = "payment_confirmed", "Payment Confirmed"
    SOURCING_ITEM = "sourcing_item", "Sourcing Item"
    SHIPPED_FROM_UK = "shipped_from_uk", "Shipped from UK"
    IN_TRANSIT = "in_transit", "In Transit"
    ARRIVED_IN_KENYA = "arrived_in_kenya", "Arrived in Kenya"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


# Happy-path sequence for forward transitions (Phase 3).
ORDER_STATUS_FLOW = [
    OrderStatus.PAYMENT_PENDING,
    OrderStatus.PAYMENT_CONFIRMED,
    OrderStatus.SOURCING_ITEM,
    OrderStatus.SHIPPED_FROM_UK,
    OrderStatus.IN_TRANSIT,
    OrderStatus.ARRIVED_IN_KENYA,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.COMPLETED,
]

TERMINAL_ORDER_STATUSES = {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
