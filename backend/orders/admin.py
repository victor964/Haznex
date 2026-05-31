from django.contrib import admin

from .models import Order, OrderStatusUpdate


class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 0
    fields = ("status", "note", "updated_by", "created_at")
    readonly_fields = ("status", "note", "updated_by", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "product",
        "client",
        "status",
        "quantity",
        "total_price",
        "shipping_method",
        "created_at",
    )
    list_filter = ("status", "shipping_method", "created_at")
    search_fields = ("order_number", "client__username", "product__name")
    readonly_fields = ("order_number", "created_at", "updated_at")
    raw_id_fields = ("product", "client", "shipping_method")
    inlines = [OrderStatusUpdateInline]


@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "updated_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order__order_number", "note")
    readonly_fields = ("order", "status", "note", "updated_by", "created_at")
    raw_id_fields = ("order", "updated_by")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
