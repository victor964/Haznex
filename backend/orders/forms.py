from django import forms

from store.models import ShippingOption


class OrderPlacementForm(forms.Form):
    shipping_method = forms.ModelChoiceField(
        queryset=ShippingOption.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        empty_label=None,
    )
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-input", "rows": 4}),
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_shipping_method(self):
        method = self.cleaned_data["shipping_method"]
        if self.product and not self.product.weight_kg:
            raise forms.ValidationError("Shipping cannot be calculated for this product.")
        return method
