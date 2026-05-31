from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "phone_number",
        "amount",
        "status",
        "stk_push_initiated",
        "manually_confirmed",
        "created_at",
    )
    list_filter = ("status", "stk_push_initiated", "manually_confirmed")
    search_fields = (
        "order__order_number",
        "phone_number",
        "mpesa_receipt_number",
        "mpesa_checkout_request_id",
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Order number")
    def order_number(self, obj):
        return obj.order.order_number
