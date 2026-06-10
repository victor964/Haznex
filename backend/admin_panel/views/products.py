from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DeleteView, FormView, ListView, UpdateView

from admin_panel.forms.products import (
    FacebookUrlForm,
    PriceBreakdownForm,
    ProductEditForm,
    ProductImagesForm,
    ProductStep1Form,
)
from store.models import PriceBreakdown, Product, ProductImage
from store.pricing import calculate_final_client_price_kes, get_gbp_to_kes_rate
from admin_panel.services.product_creation import _ensure_cloudinary_configured, create_product_bundle
from admin_panel.utils import clear_draft, get_draft, set_pricing_draft, set_product_draft
from admin_panel.mixins import HaznexAdminRequiredMixin
from admin_panel.services.facebook_scraper import scrape_facebook_listing, scrape_price_as_decimal
from store.choices import SourceType


def _serialize_form_data(cleaned_data):
    data = {}
    for key, value in cleaned_data.items():
        if value is None:
            data[key] = None
        elif hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        elif hasattr(value, "pk"):
            data[key] = value.pk
        else:
            data[key] = str(value) if hasattr(value, "quantize") else value
    return data


class ProductFetchView(HaznexAdminRequiredMixin, View):
    template_name = "admin_panel/products/fetch.html"

    def _product_initial(self, request, scrape_data=None):
        initial = {}
        draft = request.session.get("haznex_product_draft", {}).get("product")
        if draft:
            initial.update(draft)
        if scrape_data:
            if scrape_data.title:
                initial["name"] = scrape_data.title[:255]
            if scrape_data.description:
                initial["description"] = scrape_data.description
            if scrape_data.location:
                initial["location"] = scrape_data.location[:255]
            if scrape_data.image_urls and request.POST.get("action") == "scrape":
                request.session["haznex_scraped_image_urls"] = scrape_data.image_urls[:8]
                request.session.modified = True
        return initial

    def get(self, request):
        return self._render(
            request,
            FacebookUrlForm(),
            ProductStep1Form(initial=self._product_initial(request)),
        )

    def post(self, request):
        action = request.POST.get("action", "continue")

        if action == "scrape":
            url_form = FacebookUrlForm(request.POST)
            product_form = ProductStep1Form(initial=self._product_initial(request))
            if url_form.is_valid():
                result = scrape_facebook_listing(url_form.cleaned_data["facebook_url"])
                initial = self._product_initial(request, scrape_data=result)
                initial["facebook_listing_url"] = url_form.cleaned_data["facebook_url"]
                initial.setdefault("source_type", SourceType.FACEBOOK_MARKETPLACE)
                if result.scrape_error:
                    messages.warning(request, result.scrape_error)
                else:
                    messages.success(request, "Listing data loaded — review and edit below.")
                product_form = ProductStep1Form(initial=initial)
                price = scrape_price_as_decimal(result.price)
                if price is not None:
                    request.session["haznex_scrape_uk_price"] = str(price)
                request.session.modified = True
            return self._render(request, url_form, product_form)

        if action == "skip":
            return self._render(request, FacebookUrlForm(), ProductStep1Form())

        product_form = ProductStep1Form(request.POST)
        if product_form.is_valid():
            set_product_draft(request, _serialize_form_data(product_form.cleaned_data))
            return redirect("admin_panel:product_create_pricing")
        return self._render(request, FacebookUrlForm(), product_form)

    def _render(self, request, url_form, product_form):
        return render(
            request,
            self.template_name,
            {
                "url_form": url_form,
                "product_form": product_form,
                "scrape_uk_price": request.session.get("haznex_scrape_uk_price", ""),
            },
        )


class ProductPricingView(HaznexAdminRequiredMixin, FormView):
    template_name = "admin_panel/products/create_pricing.html"
    form_class = PriceBreakdownForm
    success_url = reverse_lazy("admin_panel:product_create_images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gbp_to_kes_rate"] = get_gbp_to_kes_rate()
        return context

    def dispatch(self, request, *args, **kwargs):
        if "product" not in get_draft(request):
            messages.warning(request, "Please complete product details first.")
            return redirect("admin_panel:product_fetch")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        draft = get_draft(self.request)
        if "pricing" in draft:
            for key, value in draft["pricing"].items():
                if value is not None and value != "":
                    initial[key] = Decimal(str(value)) if key != "default_shipping_option" else value
        uk_hint = self.request.session.get("haznex_scrape_uk_price")
        if uk_hint and "uk_original_price" not in initial:
            initial["uk_original_price"] = Decimal(uk_hint)
        gbp_keys = (
            "uk_original_price",
            "sourcing_fee",
            "shipping_cost",
            "transport_logistics_cost",
            "profit_margin",
        )
        if all(k in initial for k in gbp_keys):
            initial["final_client_price"] = calculate_final_client_price_kes(
                initial["uk_original_price"],
                initial["sourcing_fee"],
                initial["shipping_cost"],
                initial["transport_logistics_cost"],
                initial["profit_margin"],
            )
        return initial

    def form_valid(self, form):
        data = {}
        for key, value in form.cleaned_data.items():
            if key == "confirm_final_price":
                continue
            if key == "default_shipping_option":
                data[key] = value.pk if value else None
            elif value is not None and hasattr(value, "quantize"):
                data[key] = str(value)
            else:
                data[key] = value
        set_pricing_draft(self.request, data)
        messages.success(self.request, "Pricing saved. Upload product images next.")
        return super().form_valid(form)


class ProductImagesView(HaznexAdminRequiredMixin, View):
    template_name = "admin_panel/products/create_images.html"

    def dispatch(self, request, *args, **kwargs):
        draft = get_draft(request)
        if "product" not in draft:
            messages.warning(request, "Please complete product details first.")
            return redirect("admin_panel:product_fetch")
        if "pricing" not in draft:
            messages.warning(request, "Please complete pricing first.")
            return redirect("admin_panel:product_create_pricing")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": ProductImagesForm()},
        )

    def post(self, request):
        file_list = request.FILES.getlist("images")
        form = ProductImagesForm(request.POST, file_list=file_list)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        draft = get_draft(request)
        try:
            product = create_product_bundle(
                user=request.user,
                product_data=draft["product"],
                pricing_data=draft["pricing"],
                image_files=file_list,
                primary_index=form.cleaned_data["primary_index"],
            )
        except ImproperlyConfigured as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})
        except Exception as exc:
            messages.error(request, f"Could not save product: {exc}")
            return render(request, self.template_name, {"form": form})

        clear_draft(request)
        if "haznex_scrape_uk_price" in request.session:
            del request.session["haznex_scrape_uk_price"]
        if "haznex_scraped_image_urls" in request.session:
            del request.session["haznex_scraped_image_urls"]
        request.session.modified = True
        messages.success(request, f'Product "{product.name}" created successfully.')
        return redirect("admin_panel:product_list")


class ProductListView(HaznexAdminRequiredMixin, ListView):
    model = Product
    template_name = "admin_panel/products/list.html"
    context_object_name = "products"
    paginate_by = 25

    def get_queryset(self):
        qs = Product.objects.select_related("created_by", "price_breakdown").order_by(
            "-created_at"
        )
        is_active = self.request.GET.get("is_active")
        if is_active in ("true", "false"):
            qs = qs.filter(is_active=(is_active == "true"))
        source_type = self.request.GET.get("source_type")
        if source_type:
            qs = qs.filter(source_type=source_type)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_is_active"] = self.request.GET.get("is_active", "")
        context["filter_source_type"] = self.request.GET.get("source_type", "")
        context["search_q"] = self.request.GET.get("q", "")
        return context


class ProductEditView(HaznexAdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductEditForm
    template_name = "admin_panel/products/edit.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = self.object.images.all()
        context["image_form"] = ProductImagesForm()
        context["gbp_to_kes_rate"] = get_gbp_to_kes_rate()
        return context

    @transaction.atomic
    def form_valid(self, form):
        product = form.save()

        breakdown, _ = PriceBreakdown.objects.get_or_create(product=product)
        breakdown.uk_original_price = form.cleaned_data["uk_original_price"]
        breakdown.sourcing_fee = form.cleaned_data["sourcing_fee"]
        breakdown.shipping_cost = form.cleaned_data["shipping_cost"]
        breakdown.transport_logistics_cost = form.cleaned_data["transport_logistics_cost"]
        breakdown.profit_margin = form.cleaned_data["profit_margin"]
        breakdown.final_client_price = form.cleaned_data["final_client_price"]
        breakdown.default_shipping_option = form.cleaned_data["default_shipping_option"]
        breakdown.full_clean()
        breakdown.save()

        messages.success(self.request, f'Product "{product.name}" updated.')
        return redirect("admin_panel:product_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "set_primary" in request.POST:
            image = get_object_or_404(
                ProductImage, pk=request.POST["set_primary"], product=self.object
            )
            image.is_primary = True
            image.save()
            messages.success(request, "Primary image updated.")
            return redirect("admin_panel:product_edit", pk=self.object.pk)
        if "delete_image" in request.POST:
            image = get_object_or_404(
                ProductImage, pk=request.POST["delete_image"], product=self.object
            )
            image.delete()
            messages.success(request, "Image removed.")
            return redirect("admin_panel:product_edit", pk=self.object.pk)
        file_list = request.FILES.getlist("images")
        if file_list:
            try:
                _ensure_cloudinary_configured()
            except Exception as exc:
                messages.error(request, str(exc))
                return redirect("admin_panel:product_edit", pk=self.object.pk)
            image_form = ProductImagesForm(request.POST, file_list=file_list)
            if image_form.is_valid():
                primary_index = image_form.cleaned_data["primary_index"]
                has_primary = self.object.images.filter(is_primary=True).exists()
                for index, image_file in enumerate(file_list):
                    is_primary = index == primary_index and (
                        not has_primary or request.POST.get("replace_primary") == "on"
                    )
                    if is_primary:
                        has_primary = True
                    ProductImage.objects.create(
                        product=self.object,
                        image=image_file,
                        is_primary=is_primary,
                        display_order=self.object.images.count() + index,
                    )
                messages.success(request, f"Added {len(file_list)} image(s).")
            else:
                messages.error(request, "Could not add images. Check the form.")
            return redirect("admin_panel:product_edit", pk=self.object.pk)
        return super().post(request, *args, **kwargs)


class ProductToggleActiveView(HaznexAdminRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save(update_fields=["is_active", "updated_at"])
        state = "activated" if product.is_active else "deactivated"
        messages.success(request, f'"{product.name}" {state}.')
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_panel:product_list"))


class ProductDeleteView(HaznexAdminRequiredMixin, DeleteView):
    model = Product
    template_name = "admin_panel/products/confirm_delete.html"
    context_object_name = "product"
    success_url = reverse_lazy("admin_panel:product_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.orders.exists():
            messages.error(
                request,
                f'Cannot delete "{self.object.name}" — it has existing orders.',
            )
            return redirect("admin_panel:product_list")
        messages.success(request, f'"{self.object.name}" deleted.')
        return super().post(request, *args, **kwargs)
