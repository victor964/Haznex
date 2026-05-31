from decimal import Decimal

from django.db import migrations


def seed_shipping_options(apps, schema_editor):
    ShippingOption = apps.get_model("store", "ShippingOption")
    options = [
        {
            "code": "air",
            "name": "Air Freight",
            "base_rate_per_kg": Decimal("1500.00"),
            "estimated_delivery_days": 7,
            "display_order": 1,
        },
        {
            "code": "sea",
            "name": "Sea Freight",
            "base_rate_per_kg": Decimal("450.00"),
            "estimated_delivery_days": 45,
            "display_order": 2,
        },
    ]
    for data in options:
        ShippingOption.objects.update_or_create(code=data["code"], defaults=data)


def unseed_shipping_options(apps, schema_editor):
    ShippingOption = apps.get_model("store", "ShippingOption")
    ShippingOption.objects.filter(code__in=["air", "sea"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_shipping_options, unseed_shipping_options),
    ]
