from django.urls import path

from .views import ClientLoginView, ClientLogoutView, ClientRegisterView

app_name = "accounts"

urlpatterns = [
    path("register/", ClientRegisterView.as_view(), name="register"),
    path("login/", ClientLoginView.as_view(), name="login"),
    path("logout/", ClientLogoutView.as_view(), name="logout"),
]
