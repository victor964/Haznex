from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy


class ClientRequiredMixin(LoginRequiredMixin):
    """Require authenticated non-admin client."""

    login_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile = getattr(request.user, "profile", None)
        if profile and profile.is_admin:
            messages.info(request, "Admin accounts use the Haznex admin panel.")
            return redirect("admin_panel:dashboard")
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
