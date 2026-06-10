from decimal import Decimal

from cloudinary.models import CloudinaryField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from .choices import ProductCondition, SourceType

MONEY_VALIDATORS = [MinValueValidator(Decimal("0"))]


class ShippingOption(models.Model):
    code = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    base_rate_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="KES per kg",
    )
    estimated_delivery_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon_emoji = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def _generate_unique_slug(self):
        base_slug = slugify(self.name) or "category"
        slug = base_slug
        counter = 2
        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=ProductCondition.choices)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="products_created",
    )
    facebook_listing_url = models.URLField(max_length=500, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return self.name

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()

    @property
    def final_client_price(self):
        breakdown = getattr(self, "price_breakdown", None)
        if breakdown is None:
            return None
        return breakdown.final_client_price

    def _generate_unique_slug(self):
        base_slug = slugify(self.name) or "product"
        slug = base_slug
        counter = 2
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def clean(self):
        super().clean()
        if self.created_by_id:
            profile = getattr(self.created_by, "profile", None)
            if profile is None or not profile.is_admin:
                raise ValidationError(
                    {"created_by": "Only VH Bridge admins can create products."}
                )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = CloudinaryField("image", folder="vhbridge/products")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "display_order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_primary=True),
                name="unique_primary_image_per_product",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} — image {self.pk}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class PriceBreakdown(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="price_breakdown",
    )
    uk_original_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="GBP — original UK listing price",
    )
    sourcing_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="GBP",
    )
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="GBP — shipping for default method at listing time",
    )
    transport_logistics_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="GBP",
    )
    profit_margin = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="GBP — absolute margin",
    )
    final_client_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        help_text="KES — price shown on storefront",
    )
    default_shipping_option = models.ForeignKey(
        ShippingOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pricing for {self.product.name}"

    def clean(self):
        super().clean()
        from store.pricing import calculate_final_client_price_kes, gbp_total, get_gbp_to_kes_rate

        expected = calculate_final_client_price_kes(
            self.uk_original_price,
            self.sourcing_fee,
            self.shipping_cost,
            self.transport_logistics_cost,
            self.profit_margin,
        )
        if self.final_client_price != expected:
            total_gbp = gbp_total(
                self.uk_original_price,
                self.sourcing_fee,
                self.shipping_cost,
                self.transport_logistics_cost,
                self.profit_margin,
            )
            raise ValidationError(
                {
                    "final_client_price": (
                        f"Must equal total GBP ({total_gbp}) × rate "
                        f"({get_gbp_to_kes_rate()}) = {expected} KES."
                    )
                }
            )
