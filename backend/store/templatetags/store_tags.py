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
def source_flag_code(value):
    """Return static flag asset code for a product source_type."""
    if value == SourceType.FACEBOOK_MARKETPLACE:
        return "uk"
    if value == SourceType.LOCAL:
        return "ke"
    return ""


@register.inclusion_tag("store/partials/_source_type_badge.html")
def source_type_badge(source_type):
    if source_type == SourceType.FACEBOOK_MARKETPLACE:
        return {"flag_code": "uk", "label": "EX-UK Product"}
    if source_type == SourceType.LOCAL:
        return {"flag_code": "ke", "label": "Local Product"}
    return {"flag_code": "", "label": source_label(source_type)}


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Build a URL query string, preserving GET params unless overridden."""
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()


@register.filter
def condition_badge_class(value):
    mapping = {
        ProductCondition.NEW: "badge-new",
        ProductCondition.USED: "badge-used",
        ProductCondition.REFURBISHED: "badge-refurbished",
    }
    return mapping.get(value, "badge-source")
