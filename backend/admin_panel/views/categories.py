from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from admin_panel.forms.categories import CategoryForm
from admin_panel.mixins import HaznexAdminRequiredMixin
from store.models import Category


class CategoryListView(HaznexAdminRequiredMixin, ListView):
    model = Category
    template_name = "admin_panel/categories/list.html"
    context_object_name = "categories"
    paginate_by = 25

    def get_queryset(self):
        return (
            Category.objects.annotate(
                active_product_count=Count(
                    "products",
                    filter=Q(products__is_active=True),
                )
            )
            .order_by("display_order", "name")
        )


class CategoryCreateView(HaznexAdminRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "admin_panel/categories/form.html"
    success_url = reverse_lazy("admin_panel:category_list")

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Create Category"
        context["submit_label"] = "Create category"
        return context


class CategoryEditView(HaznexAdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "admin_panel/categories/form.html"
    context_object_name = "category"
    success_url = reverse_lazy("admin_panel:category_list")

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit Category"
        context["submit_label"] = "Save changes"
        return context


class CategoryToggleActiveView(HaznexAdminRequiredMixin, View):
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.is_active = not category.is_active
        category.save(update_fields=["is_active"])
        state = "activated" if category.is_active else "deactivated"
        messages.success(request, f'"{category.name}" {state}.')
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_panel:category_list"))


class CategoryDeleteView(HaznexAdminRequiredMixin, DeleteView):
    model = Category
    template_name = "admin_panel/categories/confirm_delete.html"
    context_object_name = "category"
    success_url = reverse_lazy("admin_panel:category_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.products.exists():
            messages.error(
                request,
                f'Cannot delete "{self.object.name}" | it has products assigned. '
                "Reassign or remove products first.",
            )
            return redirect("admin_panel:category_list")
        messages.success(request, f'"{self.object.name}" deleted.')
        return super().post(request, *args, **kwargs)
