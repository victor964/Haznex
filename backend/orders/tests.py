from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from orders.models import Order, OrderStatusUpdate
from store.choices import ORDER_STATUS_FLOW, OrderStatus
from store.models import PriceBreakdown, Product, ShippingOption
from store.pricing import calculate_final_client_price_kes


class OrderModelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_orders",
            password="testpass123",
        )
        self.admin.profile.is_admin = True
        self.admin.profile.save()

        self.client_user = User.objects.create_user(
            username="client_orders",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="other_client",
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
            name="Order Test Product",
            description="For order tests",
            condition="used",
            source_type="local",
            location="Nairobi",
            is_active=True,
            created_by=self.admin,
            weight_kg=Decimal("1.000"),
        )
        unit_price = calculate_final_client_price_kes(
            Decimal("80.00"),
            Decimal("5.00"),
            Decimal("10.00"),
            Decimal("3.00"),
            Decimal("7.00"),
        )
        PriceBreakdown.objects.create(
            product=self.product,
            uk_original_price=Decimal("80.00"),
            sourcing_fee=Decimal("5.00"),
            shipping_cost=Decimal("10.00"),
            transport_logistics_cost=Decimal("3.00"),
            profit_margin=Decimal("7.00"),
            final_client_price=unit_price,
            default_shipping_option=self.shipping,
        )
        self.unit_price = unit_price

    def _create_order(self, client_user=None):
        user = client_user or self.client_user
        shipping_fee = self.shipping.base_rate_per_kg * self.product.weight_kg
        total = self.unit_price + shipping_fee
        return Order.objects.create(
            product=self.product,
            client=user,
            shipping_method=self.shipping,
            quantity=1,
            delivery_address="123 Test Street, Nairobi",
            unit_price=self.unit_price,
            shipping_fee=shipping_fee,
            local_delivery_fee=Decimal("0"),
            total_price=total,
            status=OrderStatus.PAYMENT_PENDING,
        )

    @patch("orders.models.date")
    def test_generate_order_number_format(self, mock_date):
        mock_date.today.return_value = date(2026, 5, 31)
        order_number = Order._generate_order_number()
        self.assertRegex(order_number, r"^VH-20260531-\d{4}$")

        Order.objects.create(
            order_number=order_number,
            product=self.product,
            client=self.client_user,
            shipping_method=self.shipping,
            quantity=1,
            delivery_address="123 Test Street, Nairobi",
            unit_price=self.unit_price,
            shipping_fee=Decimal("1500.00"),
            local_delivery_fee=Decimal("0"),
            total_price=self.unit_price + Decimal("1500.00"),
        )
        next_number = Order._generate_order_number()
        self.assertEqual(next_number, "VH-20260531-0002")

    def test_status_update_syncs_order_status(self):
        order = self._create_order()
        self.assertEqual(order.status, OrderStatus.PAYMENT_PENDING)

        OrderStatusUpdate.objects.create(
            order=order,
            status=OrderStatus.PAYMENT_CONFIRMED,
            note="Payment verified by admin",
            updated_by=self.admin,
        )

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PAYMENT_CONFIRMED)

    def test_get_next_status_for_each_stage(self):
        for index, status in enumerate(ORDER_STATUS_FLOW):
            next_status = OrderStatusUpdate.get_next_status(status)
            if index + 1 < len(ORDER_STATUS_FLOW):
                self.assertEqual(next_status, ORDER_STATUS_FLOW[index + 1])
            else:
                self.assertIsNone(next_status)

        self.assertIsNone(OrderStatusUpdate.get_next_status(OrderStatus.CANCELLED))

    def test_other_client_order_tracking_returns_404(self):
        order = self._create_order()
        client = Client()
        client.login(username="other_client", password="testpass123")
        response = client.get(
            reverse("orders:order_detail", kwargs={"order_number": order.order_number})
        )
        self.assertEqual(response.status_code, 404)
