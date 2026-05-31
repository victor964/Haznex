from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView

from .forms import ClientLoginForm, ClientRegistrationForm


class ClientRegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = ClientRegistrationForm
    success_url = reverse_lazy("store:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            if profile and profile.is_admin:
                return redirect("admin_panel:dashboard")
            next_url = request.GET.get("next")
            return redirect(next_url or reverse("store:home"))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.GET.get("next") or reverse("store:home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome to Haznex! Your account has been created.")
        return super().form_valid(form)


class ClientLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = ClientLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.is_admin:
            return reverse("admin_panel:dashboard")
        return self.request.GET.get("next") or reverse("store:home")

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember_me")
        if not remember:
            self.request.session.set_expiry(0)
        response = super().form_valid(form)
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.is_admin:
            messages.info(self.request, "Redirected to Haznex admin panel.")
        else:
            messages.success(self.request, "Welcome back!")
        return response


class ClientLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.info(request, "You have been logged out.")
        return response
