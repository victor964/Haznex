from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "is_admin", "created_at")
    list_filter = ("is_admin",)
    search_fields = ("user__username", "user__email", "phone")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
