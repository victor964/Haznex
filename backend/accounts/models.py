from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    is_admin = models.BooleanField(
        default=False,
        help_text="VH Bridge admin (Victor or Hazel) — can post products and update orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self):
        suffix = " (Admin)" if self.is_admin else ""
        return f"{self.user.username}{suffix}"
