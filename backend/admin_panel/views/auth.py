from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from admin_panel.forms.auth import HaznexAuthenticationForm


class HaznexRedirectView(View):
    def get(self, request):
        profile = getattr(request.user, "profile", None)
        if request.user.is_authenticated and profile and profile.is_admin:
            return redirect("admin_panel:dashboard")
        return redirect("admin_panel:login")


class HaznexLoginView(LoginView):
    template_name = "admin_panel/login.html"
    authentication_form = HaznexAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("admin_panel:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            if profile and profile.is_admin:
                return redirect("admin_panel:dashboard")
            if profile and not profile.is_admin:
                logout(request)
                messages.error(
                    request,
                    "This account does not have Haznex admin access.",
                )
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        profile = getattr(user, "profile", None)
        if profile is None or not profile.is_admin:
            logout(self.request)
            messages.error(
                self.request,
                "This account does not have Haznex admin access.",
            )
            return self.form_invalid(form)
        messages.success(self.request, f"Welcome back, {user.get_username()}.")
        return super().form_valid(form)


class HaznexLogoutView(LogoutView):
    next_page = reverse_lazy("admin_panel:login")

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out of Haznex admin.")
        return super().dispatch(request, *args, **kwargs)
