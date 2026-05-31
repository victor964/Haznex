SESSION_DRAFT_KEY = "haznex_product_draft"


def get_draft(request):
    return request.session.get(SESSION_DRAFT_KEY, {})


def set_product_draft(request, product_data):
    draft = get_draft(request)
    draft["product"] = product_data
    request.session[SESSION_DRAFT_KEY] = draft
    request.session.modified = True


def set_pricing_draft(request, pricing_data):
    draft = get_draft(request)
    draft["pricing"] = pricing_data
    request.session[SESSION_DRAFT_KEY] = draft
    request.session.modified = True


def clear_draft(request):
    if SESSION_DRAFT_KEY in request.session:
        del request.session[SESSION_DRAFT_KEY]
        request.session.modified = True


def require_product_draft(view_func):
    """Redirect to fetch step if product draft missing."""

    def wrapper(self, request, *args, **kwargs):
        draft = get_draft(request)
        if "product" not in draft:
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.warning(request, "Please complete product details first.")
            return redirect("admin_panel:product_fetch")
        return view_func(self, request, *args, **kwargs)

    return wrapper
