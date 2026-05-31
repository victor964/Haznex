from django.contrib.auth.forms import AuthenticationForm


class HaznexAuthenticationForm(AuthenticationForm):
    """Login form for the Haznex admin panel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "haznex-input")
