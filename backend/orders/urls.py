from django.urls import path

from .views import ClientOrderListView, OrderTrackingView

app_name = "orders"

urlpatterns = [
    path("", ClientOrderListView.as_view(), name="order_list"),
    path("<str:order_number>/", OrderTrackingView.as_view(), name="order_detail"),
]
