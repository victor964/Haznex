from django.db.models import Count, Q
from django.views.generic import DetailView, ListView, TemplateView

from store.models import Category, Product


class HomeView(TemplateView):
    template_name = "store/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_products"] = (
            Product.objects.filter(is_active=True, price_breakdown__isnull=False)
            .select_related("price_breakdown")
            .prefetch_related("images")[:6]
        )
        context["categories"] = (
            Category.objects.filter(is_active=True)
            .annotate(
                product_count=Count(
                    "products",
                    filter=Q(
                        products__is_active=True,
                        products__price_breakdown__isnull=False,
                    ),
                )
            )
            .filter(product_count__gt=0)
            .order_by("display_order", "name")
        )
        return context


class ActiveProductQuerysetMixin:
    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, price_breakdown__isnull=False)
            .select_related("category", "price_breakdown")
            .prefetch_related("images")
        )


def _pagination_window(page_obj, window=2):
    """Build page numbers with ellipsis for pagination UI."""
    paginator = page_obj.paginator
    if paginator.num_pages <= 1:
        return []
    current = page_obj.number
    total = paginator.num_pages
    page_set = set(range(max(1, current - window), min(total, current + window) + 1))
    page_set.add(1)
    page_set.add(total)
    sorted_pages = sorted(page_set)
    result = []
    prev = None
    for page_num in sorted_pages:
        if prev is not None and page_num - prev > 1:
            result.append("ellipsis")
        result.append(page_num)
        prev = page_num
    return result


class ProductListView(ActiveProductQuerysetMixin, ListView):
    template_name = "store/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        category_slug = self.request.GET.get("category", "").strip()
        condition = self.request.GET.get("condition", "").strip()
        source_type = self.request.GET.get("source_type", "").strip()

        if q:
            qs = qs.filter(name__icontains=q)
        if category_slug:
            qs = qs.filter(category__slug=category_slug, category__is_active=True)
        if condition:
            qs = qs.filter(condition=condition)
        if source_type:
            qs = qs.filter(source_type=source_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["active_category"] = self.request.GET.get("category", "").strip()
        context["active_condition"] = self.request.GET.get("condition", "")
        context["active_source_type"] = self.request.GET.get("source_type", "")
        context["categories"] = Category.objects.filter(is_active=True).order_by(
            "display_order", "name"
        )
        page_obj = context.get("page_obj")
        if page_obj:
            context["pagination_pages"] = _pagination_window(page_obj)
        return context


class ProductDetailView(ActiveProductQuerysetMixin, DetailView):
    template_name = "store/product_detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        import json

        from store.models import ShippingOption

        context = super().get_context_data(**kwargs)
        product = self.object
        shipping_options = ShippingOption.objects.filter(is_active=True)
        shipping_costs = {}
        options_with_cost = []
        for option in shipping_options:
            if product.weight_kg:
                cost = option.base_rate_per_kg * product.weight_kg
                shipping_costs[str(option.pk)] = float(cost)
                options_with_cost.append({"option": option, "cost": cost})
            else:
                shipping_costs[str(option.pk)] = None
                options_with_cost.append({"option": option, "cost": None})

        context["shipping_options"] = shipping_options
        context["options_with_cost"] = options_with_cost
        context["shipping_costs_json"] = json.dumps(shipping_costs)
        context["images"] = product.images.all()
        context["can_order"] = bool(
            product.weight_kg and product.final_client_price
        )
        context["unit_price"] = float(product.final_client_price) if product.final_client_price else None
        return context
