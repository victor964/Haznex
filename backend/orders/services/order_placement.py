from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from store.choices import OrderStatus
from store.models import Product, ShippingOption

from orders.models import Order

MONEY_QUANT = Decimal("0.01")


def quantize_money(amount):
    """Round to 2 decimal places for KES fields on Order."""
    return Decimal(amount).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def calculate_shipping_fee(shipping_option, weight_kg):
    if not weight_kg:
        return None
    raw = shipping_option.base_rate_per_kg * Decimal(str(weight_kg))
    return quantize_money(raw)


@transaction.atomic
def create_client_order(*, product, client, shipping_method, delivery_address, quantity=1):
    if not product.is_active:
        raise ValueError("Product is not available.")
    if not product.weight_kg or not product.final_client_price:
        raise ValueError("Product cannot be ordered.")

    unit_price = product.final_client_price
    shipping_fee = calculate_shipping_fee(shipping_method, product.weight_kg)
    if shipping_fee is None:
        raise ValueError("Shipping fee cannot be calculated.")

    local_delivery_fee = Decimal("0.00")
    total_price = quantize_money(
        (unit_price * quantity) + shipping_fee + local_delivery_fee
    )

    order = Order(
        product=product,
        client=client,
        shipping_method=shipping_method,
        quantity=quantity,
        delivery_address=delivery_address,
        unit_price=unit_price,
        shipping_fee=shipping_fee,
        local_delivery_fee=local_delivery_fee,
        total_price=total_price,
        status=OrderStatus.PAYMENT_PENDING,
    )
    order.full_clean()
    order.save()

    profile = client.profile
    if profile.delivery_address != delivery_address:
        profile.delivery_address = delivery_address
        profile.save(update_fields=["delivery_address", "updated_at"])

    return order
