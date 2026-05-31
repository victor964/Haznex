from django import forms

from admin_panel.services.order_status import get_allowed_next_statuses
from store.choices import OrderStatus


class OrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=[], widget=forms.Select(attrs={"class": "haznex-input"}))
    note = forms.CharField(
        widget=forms.Textarea(attrs={"class": "haznex-input", "rows": 3}),
        label="Note for client / internal record",
    )

    def __init__(self, *args, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order
        if order:
            choices = get_allowed_next_statuses(order.status)
            self.fields["status"].choices = [("", "Select next status")] + choices

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if not status:
            raise forms.ValidationError("Select a status.")
        allowed = [c[0] for c in get_allowed_next_statuses(self.order.status)]
        if status not in allowed:
            raise forms.ValidationError("That status transition is not allowed.")
        return status
