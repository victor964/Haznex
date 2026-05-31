from django import template

from store.choices import ProductCondition, SourceType

register = template.Library()


@register.filter
def split(value, delimiter=" "):
    if not value:
        return []
    return value.split(delimiter)


@register.filter
def kes(value):
    """Format a number as KES with comma separators."""
    if value is None:
        return "N/A"
    try:
        amount = float(value)
        if amount == int(amount):
            return f"KES {int(amount):,}"
        return f"KES {amount:,.2f}"
    except (TypeError, ValueError):
        return value


@register.filter
def source_label(value):
    if value == SourceType.FACEBOOK_MARKETPLACE:
        return "EX-UK"
    if value == SourceType.LOCAL:
        return "Local"
    return value


@register.filter
def condition_badge_class(value):
    mapping = {
        ProductCondition.NEW: "badge-new",
        ProductCondition.USED: "badge-used",
        ProductCondition.REFURBISHED: "badge-refurbished",
    }
    return mapping.get(value, "badge-source")
