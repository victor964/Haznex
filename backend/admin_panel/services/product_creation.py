from decimal import Decimal

import cloudinary
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from store.models import PriceBreakdown, Product, ProductImage


def _ensure_cloudinary_configured():
    storage = settings.CLOUDINARY_STORAGE
    if not all((storage.get("CLOUD_NAME"), storage.get("API_KEY"), storage.get("API_SECRET"))):
        raise ImproperlyConfigured(
            "Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, "
            "and CLOUDINARY_API_SECRET to your .env file (see .env.example), then restart the server."
        )
    cloudinary.config(
        cloud_name=storage["CLOUD_NAME"],
        api_key=storage["API_KEY"],
        api_secret=storage["API_SECRET"],
        secure=True,
    )


@transaction.atomic
def create_product_bundle(user, product_data, pricing_data, image_files, primary_index=0):
    _ensure_cloudinary_configured()

    category_id = product_data.get("category")
    if category_id in ("", None):
        category_id = None

    product = Product(
        name=product_data["name"],
        description=product_data["description"],
        condition=product_data["condition"],
        source_type=product_data["source_type"],
        location=product_data["location"],
        facebook_listing_url=product_data.get("facebook_listing_url") or "",
        category_id=category_id,
        weight_kg=_decimal_or_none(product_data.get("weight_kg")),
        is_active=False,
        created_by=user,
    )
    product.full_clean()
    product.save()

    breakdown = PriceBreakdown(
        product=product,
        uk_original_price=Decimal(str(pricing_data["uk_original_price"])),
        sourcing_fee=Decimal(str(pricing_data["sourcing_fee"])),
        shipping_cost=Decimal(str(pricing_data["shipping_cost"])),
        transport_logistics_cost=Decimal(str(pricing_data["transport_logistics_cost"])),
        profit_margin=Decimal(str(pricing_data["profit_margin"])),
        final_client_price=Decimal(str(pricing_data["final_client_price"])),
        default_shipping_option_id=pricing_data.get("default_shipping_option"),
    )
    breakdown.full_clean()
    breakdown.save()

    for index, image_file in enumerate(image_files):
        ProductImage.objects.create(
            product=product,
            image=image_file,
            is_primary=(index == primary_index),
            display_order=index,
        )

    return product


def _decimal_or_none(value):
    if value is None or value == "":
        return None
    return Decimal(str(value))
