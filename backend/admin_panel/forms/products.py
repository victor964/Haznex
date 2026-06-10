from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from store.choices import ProductCondition, SourceType
from store.models import Category, PriceBreakdown, Product, ShippingOption
from store.pricing import calculate_final_client_price_kes

GBP_FIELD_HELP = "Enter amount in GBP (£)"


class FacebookUrlForm(forms.Form):
    facebook_url = forms.URLField(
        label="Facebook Marketplace URL",
        max_length=500,
        widget=forms.URLInput(
            attrs={
                "class": "haznex-input",
                "placeholder": "https://www.facebook.com/marketplace/item/...",
            }
        ),
    )


class ProductStep1Form(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "condition",
            "source_type",
            "location",
            "facebook_listing_url",
            "weight_kg",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "haznex-input"}),
            "category": forms.Select(attrs={"class": "haznex-input"}),
            "description": forms.Textarea(attrs={"class": "haznex-input", "rows": 5}),
            "condition": forms.Select(attrs={"class": "haznex-input"}),
            "source_type": forms.Select(attrs={"class": "haznex-input"}),
            "location": forms.TextInput(attrs={"class": "haznex-input"}),
            "facebook_listing_url": forms.URLInput(attrs={"class": "haznex-input"}),
            "weight_kg": forms.NumberInput(attrs={"class": "haznex-input", "step": "0.001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by(
            "display_order", "name"
        )
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Select a category (optional)"
        self.fields["source_type"].initial = SourceType.FACEBOOK_MARKETPLACE
        self.fields["condition"].initial = ProductCondition.USED


def _validate_final_price_gbp_to_kes(cleaned):
    expected = calculate_final_client_price_kes(
        cleaned["uk_original_price"],
        cleaned["sourcing_fee"],
        cleaned["shipping_cost"],
        cleaned["transport_logistics_cost"],
        cleaned["profit_margin"],
    )
    if cleaned["final_client_price"] != expected:
        raise ValidationError(
            {
                "final_client_price": (
                    f"Must equal total GBP converted to KES ({expected} KES). "
                    "Use the calculator or adjust the GBP fields."
                )
            }
        )


class PriceBreakdownForm(forms.ModelForm):
    confirm_final_price = forms.BooleanField(
        required=True,
        label="I confirm this final client price is correct",
    )

    class Meta:
        model = PriceBreakdown
        fields = [
            "uk_original_price",
            "sourcing_fee",
            "shipping_cost",
            "transport_logistics_cost",
            "profit_margin",
            "final_client_price",
            "default_shipping_option",
        ]
        widgets = {
            "uk_original_price": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_uk_original_price"}
            ),
            "sourcing_fee": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_sourcing_fee"}
            ),
            "shipping_cost": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_shipping_cost"}
            ),
            "transport_logistics_cost": forms.NumberInput(
                attrs={
                    "class": "haznex-input haznex-gbp-field",
                    "step": "0.01",
                    "id": "id_transport_logistics_cost",
                }
            ),
            "profit_margin": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_profit_margin"}
            ),
            "final_client_price": forms.NumberInput(
                attrs={
                    "class": "haznex-input haznex-final-kes-field",
                    "step": "0.01",
                    "id": "id_final_client_price",
                    "readonly": "readonly",
                }
            ),
            "default_shipping_option": forms.Select(attrs={"class": "haznex-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (
            "uk_original_price",
            "sourcing_fee",
            "shipping_cost",
            "transport_logistics_cost",
            "profit_margin",
        ):
            self.fields[name].help_text = GBP_FIELD_HELP
        self.fields["final_client_price"].help_text = "KES — auto-calculated from GBP total × exchange rate"
        self.fields["default_shipping_option"].queryset = ShippingOption.objects.filter(
            is_active=True
        )
        self.fields["default_shipping_option"].required = False

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        _validate_final_price_gbp_to_kes(cleaned)
        return cleaned


class ProductImagesForm(forms.Form):
    """Image files come from request.FILES.getlist('images') — not a ModelForm field."""

    primary_index = forms.IntegerField(
        min_value=0,
        initial=0,
        label="Primary image index (0 = first file)",
        widget=forms.NumberInput(attrs={"class": "haznex-input", "id": "id_primary_index"}),
    )

    def __init__(self, *args, file_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_list = file_list or []

    def clean(self):
        cleaned = super().clean()
        if not self.file_list:
            raise ValidationError("Upload at least one product image.")
        primary = cleaned.get("primary_index", 0)
        if primary < 0 or primary >= len(self.file_list):
            raise ValidationError(
                {"primary_index": f"Must be between 0 and {len(self.file_list) - 1}."}
            )
        return cleaned


class ProductEditForm(forms.ModelForm):
    """Combined product + pricing fields for edit view."""

    uk_original_price = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    sourcing_fee = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    shipping_cost = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    transport_logistics_cost = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0")
    )
    profit_margin = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    final_client_price = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    default_shipping_option = forms.ModelChoiceField(
        queryset=ShippingOption.objects.filter(is_active=True),
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "condition",
            "source_type",
            "location",
            "facebook_listing_url",
            "weight_kg",
            "is_active",
        ]
        widgets = {
            **ProductStep1Form.Meta.widgets,
            "is_active": forms.CheckboxInput(attrs={"class": "haznex-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by(
            "display_order", "name"
        )
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Select a category (optional)"
        gbp_widgets = {
            "uk_original_price": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_uk_original_price"}
            ),
            "sourcing_fee": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_sourcing_fee"}
            ),
            "shipping_cost": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_shipping_cost"}
            ),
            "transport_logistics_cost": forms.NumberInput(
                attrs={
                    "class": "haznex-input haznex-gbp-field",
                    "step": "0.01",
                    "id": "id_transport_logistics_cost",
                }
            ),
            "profit_margin": forms.NumberInput(
                attrs={"class": "haznex-input haznex-gbp-field", "step": "0.01", "id": "id_profit_margin"}
            ),
            "final_client_price": forms.NumberInput(
                attrs={
                    "class": "haznex-input",
                    "step": "0.01",
                    "id": "id_final_client_price",
                    "readonly": "readonly",
                }
            ),
        }
        for name, widget in gbp_widgets.items():
            self.fields[name].widget = widget
        for name in (
            "uk_original_price",
            "sourcing_fee",
            "shipping_cost",
            "transport_logistics_cost",
            "profit_margin",
        ):
            self.fields[name].help_text = GBP_FIELD_HELP
        self.fields["final_client_price"].help_text = "KES — auto-calculated from GBP total × exchange rate"
        breakdown = getattr(self.instance, "price_breakdown", None)
        if breakdown:
            for field in (
                "uk_original_price",
                "sourcing_fee",
                "shipping_cost",
                "transport_logistics_cost",
                "profit_margin",
                "final_client_price",
                "default_shipping_option",
            ):
                self.fields[field].initial = getattr(breakdown, field)

    def clean(self):
        cleaned = super().clean()
        _validate_final_price_gbp_to_kes(cleaned)
        return cleaned
