from django.urls import path

from .views import (
    InitiateStkPushView,
    ManualPaymentConfirmView,
    MpesaCallbackView,
    PaymentPageView,
    PaymentStatusView,
)

app_name = "payments"

urlpatterns = [
    path("callback/", MpesaCallbackView.as_view(), name="callback"),
    path("<str:order_number>/pay/", PaymentPageView.as_view(), name="pay"),
    path("<str:order_number>/initiate/", InitiateStkPushView.as_view(), name="initiate"),
    path(
        "<str:order_number>/manual-confirm/",
        ManualPaymentConfirmView.as_view(),
        name="manual_confirm",
    ),
    path("<str:order_number>/status/", PaymentStatusView.as_view(), name="status"),
]
