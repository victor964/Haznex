from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


def get_gbp_to_kes_rate():
    return Decimal(str(settings.GBP_TO_KES_RATE))


def gbp_total(
    uk_original_price,
    sourcing_fee,
    shipping_cost,
    transport_logistics_cost,
    profit_margin,
):
    return (
        Decimal(str(uk_original_price))
        + Decimal(str(sourcing_fee))
        + Decimal(str(shipping_cost))
        + Decimal(str(transport_logistics_cost))
        + Decimal(str(profit_margin))
    )


def calculate_final_client_price_kes(
    uk_original_price,
    sourcing_fee,
    shipping_cost,
    transport_logistics_cost,
    profit_margin,
):
    """Sum all GBP inputs, convert to KES for storefront price."""
    total_gbp = gbp_total(
        uk_original_price,
        sourcing_fee,
        shipping_cost,
        transport_logistics_cost,
        profit_margin,
    )
    return (total_gbp * get_gbp_to_kes_rate()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
