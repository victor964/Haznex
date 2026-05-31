from django.urls import path

from django.views.generic import RedirectView

from admin_panel.views.auth import HaznexLoginView, HaznexLogoutView, HaznexRedirectView
from admin_panel.views.dashboard import DashboardView
from admin_panel.views.orders import (
    CancelOrderView,
    ConfirmPaymentView,
    OrderDetailView,
    OrderListView,
)
from admin_panel.views.products import (
    ProductDeleteView,
    ProductEditView,
    ProductFetchView,
    ProductImagesView,
    ProductListView,
    ProductPricingView,
    ProductToggleActiveView,
)

app_name = "admin_panel"

urlpatterns = [
    path("", HaznexRedirectView.as_view(), name="index"),
    path("login/", HaznexLoginView.as_view(), name="login"),
    path("logout/", HaznexLogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/fetch/", ProductFetchView.as_view(), name="product_fetch"),
    path("products/<int:pk>/edit/", ProductEditView.as_view(), name="product_edit"),
    path("products/<int:pk>/toggle-active/", ProductToggleActiveView.as_view(), name="product_toggle_active"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("products/create/pricing/", ProductPricingView.as_view(), name="product_create_pricing"),
    path("products/create/images/", ProductImagesView.as_view(), name="product_create_images"),
    path(
        "products/create/",
        RedirectView.as_view(pattern_name="admin_panel:product_fetch", permanent=False),
        name="product_create",
    ),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path(
        "orders/<int:pk>/confirm-payment/",
        ConfirmPaymentView.as_view(),
        name="confirm_payment",
    ),
    path(
        "orders/<int:pk>/cancel/",
        CancelOrderView.as_view(),
        name="cancel_order",
    ),
]
