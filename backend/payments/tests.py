from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from orders.models import Order
from payments.models import Payment
from store.choices import OrderStatus
from store.models import PriceBreakdown, Product, ShippingOption
from store.pricing import calculate_final_client_price_kes

from .utils import normalize_mpesa_phone


class PaymentUtilsTests(TestCase):
    def test_normalize_mpesa_phone_07_format(self):
        self.assertEqual(normalize_mpesa_phone("0712345678"), "254712345678")

    def test_normalize_mpesa_phone_254_format(self):
        self.assertEqual(normalize_mpesa_phone("254712345678"), "254712345678")

    def test_normalize_mpesa_phone_invalid(self):
        self.assertIsNone(normalize_mpesa_phone("12345"))


class ManualPaymentConfirmTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_pay",
            password="testpass123",
        )
        self.admin.profile.is_admin = True
        self.admin.profile.save()

        self.client_user = User.objects.create_user(
            username="client_pay",
            password="testpass123",
        )

        self.shipping = ShippingOption.objects.filter(code="air").first()
        if not self.shipping:
            self.shipping = ShippingOption.objects.create(
                code="air",
                name="Air Freight",
                base_rate_per_kg=Decimal("1500.00"),
                estimated_delivery_days=14,
            )

        self.product = Product.objects.create(
            name="Payment Test Product",
            description="For payment tests",
            condition="new",
            source_type="local",
            location="Nairobi",
            is_active=True,
            created_by=self.admin,
            weight_kg=Decimal("1.000"),
        )
        unit_price = calculate_final_client_price_kes(
            Decimal("60.00"),
            Decimal("4.00"),
            Decimal("8.00"),
            Decimal("2.00"),
            Decimal("6.00"),
        )
        PriceBreakdown.objects.create(
            product=self.product,
            uk_original_price=Decimal("60.00"),
            sourcing_fee=Decimal("4.00"),
            shipping_cost=Decimal("8.00"),
            transport_logistics_cost=Decimal("2.00"),
            profit_margin=Decimal("6.00"),
            final_client_price=unit_price,
            default_shipping_option=self.shipping,
        )

        shipping_fee = self.shipping.base_rate_per_kg * self.product.weight_kg
        self.order = Order.objects.create(
            product=self.product,
            client=self.client_user,
            shipping_method=self.shipping,
            quantity=1,
            delivery_address="456 Pay Street, Nairobi",
            unit_price=unit_price,
            shipping_fee=shipping_fee,
            local_delivery_fee=Decimal("0"),
            total_price=unit_price + shipping_fee,
            status=OrderStatus.PAYMENT_PENDING,
        )

        self.http_client = Client()
        self.http_client.login(username="client_pay", password="testpass123")

    def test_manual_confirm_creates_payment_and_redirects(self):
        url = reverse(
            "payments:manual_confirm",
            kwargs={"order_number": self.order.order_number},
        )
        response = self.http_client.post(url, {"phone_number": "0712345678"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "orders:order_detail",
                kwargs={"order_number": self.order.order_number},
            ),
        )

        payment = Payment.objects.get(order=self.order)
        self.assertTrue(payment.manually_confirmed)
        self.assertEqual(payment.phone_number, "254712345678")
        self.assertEqual(payment.amount, self.order.total_price)
