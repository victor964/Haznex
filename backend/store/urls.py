from django.urls import path

from orders.views import OrderPlacementView

from .views import HomeView, ProductDetailView, ProductListView

app_name = "store"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path("products/<slug:slug>/order/", OrderPlacementView.as_view(), name="order_place"),
]
