from django.contrib import admin

from django.db.models import Count

from .models import Category, PriceBreakdown, Product, ProductImage, ShippingOption


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_primary", "display_order")


class PriceBreakdownInline(admin.StackedInline):
    model = PriceBreakdown
    max_num = 1
    can_delete = True
    fields = (
        "uk_original_price",
        "sourcing_fee",
        "shipping_cost",
        "transport_logistics_cost",
        "profit_margin",
        "final_client_price",
        "default_shipping_option",
    )


@admin.register(ShippingOption)
class ShippingOptionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "base_rate_per_kg",
        "estimated_delivery_days",
        "is_active",
        "display_order",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("display_order", "name")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "display_order", "product_count")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("display_order", "name")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_product_count=Count("products"))

    @admin.display(description="Products")
    def product_count(self, obj):
        return getattr(obj, "_product_count", obj.products.count())


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "category",
        "condition",
        "source_type",
        "location",
        "is_active",
        "created_by",
        "created_at",
    )
    list_filter = ("is_active", "condition", "source_type", "category", "created_at")
    search_fields = ("name", "slug", "location")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [PriceBreakdownInline, ProductImageInline]
    raw_id_fields = ("created_by",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "created_by":
            kwargs["queryset"] = kwargs.get("queryset", db_field.remote_field.model.objects.all()).filter(
                profile__is_admin=True
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "display_order", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt_text")
    raw_id_fields = ("product",)


@admin.register(PriceBreakdown)
class PriceBreakdownAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "uk_original_price",
        "final_client_price",
        "default_shipping_option",
        "updated_at",
    )
    search_fields = ("product__name",)
    raw_id_fields = ("product", "default_shipping_option")
