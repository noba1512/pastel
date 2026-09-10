from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.catalog.forms import CategoryForm, ProductForm
from apps.catalog.models import Category, Product
from apps.core.mixins import CatalogRequiredMixin


class ProductListView(CatalogRequiredMixin, ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 40

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "stock")
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(sku__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(active=True)
        context["q"] = self.request.GET.get("q", "")
        context["selected_category"] = self.request.GET.get("category", "")
        return context


class ProductCreateView(CatalogRequiredMixin, View):
    template_name = "catalog/product_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ProductForm(), "title": "Novo produto"})

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado.")
            return redirect("catalog:product_list")
        return render(request, self.template_name, {"form": form, "title": "Novo produto"})


class ProductUpdateView(CatalogRequiredMixin, View):
    template_name = "catalog/product_form.html"

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(
            request,
            self.template_name,
            {"form": ProductForm(instance=product), "title": f"Editar {product.name}"},
        )

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto atualizado.")
            return redirect("catalog:product_list")
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Editar {product.name}"},
        )


class ProductDeactivateView(CatalogRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.active = not product.active
        product.save(update_fields=["active", "updated_at"])
        state = "ativado" if product.active else "desativado"
        messages.success(request, f"Produto {state}.")
        return redirect("catalog:product_list")


class CategoryListView(CatalogRequiredMixin, ListView):
    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"


class CategoryCreateView(CatalogRequiredMixin, View):
    template_name = "catalog/category_form.html"

    def get(self, request):
        return render(
            request, self.template_name, {"form": CategoryForm(), "title": "Nova categoria"}
        )

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria cadastrada.")
            return redirect("catalog:category_list")
        return render(request, self.template_name, {"form": form, "title": "Nova categoria"})


class CategoryUpdateView(CatalogRequiredMixin, View):
    template_name = "catalog/category_form.html"

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        return render(
            request,
            self.template_name,
            {"form": CategoryForm(instance=category), "title": f"Editar {category.name}"},
        )

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada.")
            return redirect("catalog:category_list")
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Editar {category.name}"},
        )
