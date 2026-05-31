from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class HaznexAdminRequiredMixin(LoginRequiredMixin):
    """Require an authenticated user with profile.is_admin=True."""

    login_url = reverse_lazy("admin_panel:login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile = getattr(request.user, "profile", None)
        if profile is None or not profile.is_admin:
            messages.error(request, "You do not have Haznex admin access.")
            return redirect("admin_panel:login")
        return super().dispatch(request, *args, **kwargs)
