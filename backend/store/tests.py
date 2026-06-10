from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from store.models import Category, PriceBreakdown, Product, ShippingOption
from store.pricing import calculate_final_client_price_kes


class ProductPricingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_store",
            password="testpass123",
        )
        self.admin.profile.is_admin = True
        self.admin.profile.save()

        self.shipping = ShippingOption.objects.filter(code="air").first()
        if not self.shipping:
            self.shipping = ShippingOption.objects.create(
                code="air",
                name="Air Freight",
                base_rate_per_kg=Decimal("1500.00"),
                estimated_delivery_days=14,
            )

        self.product = Product.objects.create(
            name="Test Laptop",
            description="A test product",
            condition="used",
            source_type="facebook_marketplace",
            location="London, UK",
            is_active=True,
            created_by=self.admin,
            weight_kg=Decimal("2.500"),
        )

        self.breakdown = PriceBreakdown.objects.create(
            product=self.product,
            uk_original_price=Decimal("100.00"),
            sourcing_fee=Decimal("10.00"),
            shipping_cost=Decimal("20.00"),
            transport_logistics_cost=Decimal("5.00"),
            profit_margin=Decimal("15.00"),
            final_client_price=calculate_final_client_price_kes(
                Decimal("100.00"),
                Decimal("10.00"),
                Decimal("20.00"),
                Decimal("5.00"),
                Decimal("15.00"),
            ),
            default_shipping_option=self.shipping,
        )

    def test_final_client_price_returns_breakdown_value(self):
        self.assertEqual(
            self.product.final_client_price,
            self.breakdown.final_client_price,
        )

    def test_price_breakdown_clean_raises_on_mismatch(self):
        self.breakdown.final_client_price = Decimal("99999.99")
        with self.assertRaises(ValidationError) as ctx:
            self.breakdown.full_clean()
        self.assertIn("final_client_price", ctx.exception.message_dict)

    def test_inactive_product_not_in_storefront_listing(self):
        inactive = Product.objects.create(
            name="Hidden Phone",
            description="Inactive listing",
            condition="new",
            source_type="local",
            location="Nairobi",
            is_active=False,
            created_by=self.admin,
            weight_kg=Decimal("0.500"),
        )
        PriceBreakdown.objects.create(
            product=inactive,
            uk_original_price=Decimal("50.00"),
            sourcing_fee=Decimal("5.00"),
            shipping_cost=Decimal("10.00"),
            transport_logistics_cost=Decimal("2.00"),
            profit_margin=Decimal("8.00"),
            final_client_price=calculate_final_client_price_kes(
                Decimal("50.00"),
                Decimal("5.00"),
                Decimal("10.00"),
                Decimal("2.00"),
                Decimal("8.00"),
            ),
            default_shipping_option=self.shipping,
        )

        response = self.client.get(reverse("store:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, inactive.name)


class CategoryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_cat",
            password="testpass123",
        )
        self.admin.profile.is_admin = True
        self.admin.profile.save()

        self.shipping = ShippingOption.objects.filter(code="air").first()
        if not self.shipping:
            self.shipping = ShippingOption.objects.create(
                code="air",
                name="Air Freight",
                base_rate_per_kg=Decimal("1500.00"),
                estimated_delivery_days=14,
            )

        self.category = Category.objects.create(name="Gaming", icon_emoji="🎮")
        self.other_category = Category.objects.create(name="Phones")

        self.product = Product.objects.create(
            name="Gaming Console",
            description="Test",
            condition="used",
            source_type="facebook_marketplace",
            location="London, UK",
            is_active=True,
            created_by=self.admin,
            category=self.category,
            weight_kg=Decimal("3.000"),
        )
        PriceBreakdown.objects.create(
            product=self.product,
            uk_original_price=Decimal("200.00"),
            sourcing_fee=Decimal("10.00"),
            shipping_cost=Decimal("20.00"),
            transport_logistics_cost=Decimal("5.00"),
            profit_margin=Decimal("15.00"),
            final_client_price=calculate_final_client_price_kes(
                Decimal("200.00"),
                Decimal("10.00"),
                Decimal("20.00"),
                Decimal("5.00"),
                Decimal("15.00"),
            ),
            default_shipping_option=self.shipping,
        )

        self.other_product = Product.objects.create(
            name="Android Phone",
            description="Test phone",
            condition="new",
            source_type="local",
            location="Nairobi",
            is_active=True,
            created_by=self.admin,
            category=self.other_category,
            weight_kg=Decimal("0.300"),
        )
        PriceBreakdown.objects.create(
            product=self.other_product,
            uk_original_price=Decimal("100.00"),
            sourcing_fee=Decimal("10.00"),
            shipping_cost=Decimal("20.00"),
            transport_logistics_cost=Decimal("5.00"),
            profit_margin=Decimal("15.00"),
            final_client_price=calculate_final_client_price_kes(
                Decimal("100.00"),
                Decimal("10.00"),
                Decimal("20.00"),
                Decimal("5.00"),
                Decimal("15.00"),
            ),
            default_shipping_option=self.shipping,
        )

    def test_category_slug_auto_generated(self):
        self.assertEqual(self.category.slug, "gaming")

    def test_product_list_filters_by_category(self):
        response = self.client.get(
            reverse("store:product_list"),
            {"category": self.category.slug},
        )
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, self.other_product.name)

    def test_product_list_combined_filters(self):
        response = self.client.get(
            reverse("store:product_list"),
            {
                "category": self.category.slug,
                "q": "Gaming",
                "condition": "used",
            },
        )
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, self.other_product.name)

    def test_pagination_preserves_filters(self):
        for i in range(13):
            product = Product.objects.create(
                name=f"Extra Gaming Item {i}",
                description="Bulk item",
                condition="used",
                source_type="facebook_marketplace",
                location="London, UK",
                is_active=True,
                created_by=self.admin,
                category=self.category,
                weight_kg=Decimal("1.000"),
            )
            PriceBreakdown.objects.create(
                product=product,
                uk_original_price=Decimal("50.00"),
                sourcing_fee=Decimal("5.00"),
                shipping_cost=Decimal("10.00"),
                transport_logistics_cost=Decimal("2.00"),
                profit_margin=Decimal("8.00"),
                final_client_price=calculate_final_client_price_kes(
                    Decimal("50.00"),
                    Decimal("5.00"),
                    Decimal("10.00"),
                    Decimal("2.00"),
                    Decimal("8.00"),
                ),
                default_shipping_option=self.shipping,
            )

        response = self.client.get(
            reverse("store:product_list"),
            {"category": self.category.slug, "q": "Gaming", "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "page=2")
        self.assertContains(response, f"category={self.category.slug}")
        self.assertContains(response, "q=Gaming")
