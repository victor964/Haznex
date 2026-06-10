from django import forms

from store.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "icon_emoji", "display_order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "haznex-input"}),
            "description": forms.Textarea(attrs={"class": "haznex-input", "rows": 3}),
            "icon_emoji": forms.TextInput(
                attrs={"class": "haznex-input", "placeholder": "e.g. gaming emoji"}
            ),
            "display_order": forms.NumberInput(attrs={"class": "haznex-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "haznex-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields.pop("is_active", None)
