from django.contrib import messages
from django.db.models import F
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView

from apps.core.exceptions import DomainError
from apps.core.mixins import StockAdjustRequiredMixin, StockViewRequiredMixin
from apps.inventory.forms import StockAdjustForm, StockEntryForm
from apps.inventory.models import Stock, StockMovement
from apps.inventory.services import register_adjustment, register_entry


class StockListView(StockViewRequiredMixin, ListView):
    model = Stock
    template_name = "inventory/stock_list.html"
    context_object_name = "stocks"
    paginate_by = 50

    def get_queryset(self):
        queryset = Stock.objects.select_related("product", "product__category")
        situation = self.request.GET.get("situation")
        if situation == "out":
            queryset = queryset.filter(quantity=0)
        elif situation == "low":
            queryset = queryset.filter(quantity__gt=0, quantity__lte=F("minimum_quantity"))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["situation"] = self.request.GET.get("situation", "")
        return context


class StockEntryView(StockAdjustRequiredMixin, View):
    template_name = "inventory/stock_entry.html"

    def get(self, request):
        initial = {}
        product_id = request.GET.get("product")
        if product_id:
            initial["product"] = product_id
        return render(request, self.template_name, {"form": StockEntryForm(initial=initial)})

    def post(self, request):
        form = StockEntryForm(request.POST)
        if form.is_valid():
            try:
                register_entry(
                    product=form.cleaned_data["product"],
                    quantity=form.cleaned_data["quantity"],
                    user=request.user,
                    reason=form.cleaned_data.get("reason") or "",
                )
            except DomainError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Entrada de estoque registrada.")
                return redirect("inventory:stock_list")
        return render(request, self.template_name, {"form": form})


class StockAdjustView(StockAdjustRequiredMixin, View):
    template_name = "inventory/stock_adjust.html"

    def get(self, request):
        initial = {}
        product_id = request.GET.get("product")
        if product_id:
            initial["product"] = product_id
        return render(request, self.template_name, {"form": StockAdjustForm(initial=initial)})

    def post(self, request):
        form = StockAdjustForm(request.POST)
        if form.is_valid():
            try:
                register_adjustment(
                    product=form.cleaned_data["product"],
                    quantity=form.cleaned_data["quantity"],
                    user=request.user,
                    reason=form.cleaned_data["reason"],
                    increase=form.cleaned_data["direction"] == "in",
                )
            except DomainError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Ajuste de estoque registrado.")
                return redirect("inventory:stock_list")
        return render(request, self.template_name, {"form": form})


class StockMovementListView(StockViewRequiredMixin, ListView):
    model = StockMovement
    template_name = "inventory/movement_list.html"
    context_object_name = "movements"
    paginate_by = 40

    def get_queryset(self):
        return StockMovement.objects.select_related("product", "user", "sale")
