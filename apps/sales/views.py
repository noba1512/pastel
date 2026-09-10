import json
from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from apps.catalog.models import Category, Product
from apps.core.exceptions import DomainError
from apps.core.mixins import (
    CancelSaleRequiredMixin,
    SalesHistoryRequiredMixin,
    SellRequiredMixin,
)
from apps.core.permissions import can_cancel_sale, can_view_all_sales, can_view_sale
from apps.core.store import store_context
from apps.sales.forms import SaleCancelForm, SaleFilterForm
from apps.sales.cash import get_open_session
from apps.sales.models import Payment, Sale
from apps.sales.receipt_print import print_sale_receipt
from apps.sales.services import cancel_sale, complete_sale


class PdvView(SellRequiredMixin, View):
    template_name = "sales/pdv.html"

    def get(self, request):
        session = get_open_session(request.user)
        if session is None:
            messages.info(request, "Abra o caixa para começar a vender.")
            return redirect("sales:cash_open")
        products = (
            Product.objects.filter(active=True)
            .select_related("category", "stock")
            .order_by("name")
        )
        categories = Category.objects.filter(active=True, products__active=True).distinct()
        return render(
            request,
            self.template_name,
            {
                "products": products,
                "categories": categories,
                "payment_methods": Payment.Method.choices,
                "cash_session": session,
            },
        )


class PdvSearchView(SellRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        category_id = request.GET.get("category", "").strip()
        products = Product.objects.filter(active=True).select_related("category", "stock")
        if query:
            products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
        if category_id:
            products = products.filter(category_id=category_id)
        payload = []
        for product in products.order_by("name")[:80]:
            stock_qty = product.stock.quantity if hasattr(product, "stock") else 0
            payload.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "price": str(product.sale_price),
                    "category": product.category.name,
                    "category_id": product.category_id,
                    "stock": stock_qty,
                }
            )
        return JsonResponse({"products": payload})


class PdvCheckoutView(SellRequiredMixin, View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": "Pedido inválido."}, status=400)

        try:
            sale = complete_sale(
                operator=request.user,
                items=payload.get("items") or [],
                payment_method=payload.get("payment_method"),
                amount_received=payload.get("amount_received"),
                discount=payload.get("discount") or 0,
            )
        except DomainError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)

        payment = sale.payment
        printed = False
        print_method = ""
        print_error = ""
        if payload.get("print", True) is not False:
            result = print_sale_receipt(sale)
            printed = result.ok
            print_method = result.method
            print_error = result.error
        return JsonResponse(
            {
                "ok": True,
                "number": sale.number,
                "total": str(sale.total),
                "change": str(payment.change) if payment and payment.change is not None else None,
                "detail_url": reverse("sales:detail", args=[sale.pk]),
                "print_url": reverse("sales:receipt", args=[sale.pk]),
                "reprint_url": reverse("sales:print", args=[sale.pk]),
                "printed": printed,
                "print_method": print_method,
                "print_error": print_error,
            }
        )


class SaleListView(SalesHistoryRequiredMixin, ListView):
    model = Sale
    template_name = "sales/sale_list.html"
    context_object_name = "sales"
    paginate_by = 25

    def get_queryset(self):
        queryset = Sale.objects.select_related("operator").prefetch_related("payments", "items")
        if not can_view_all_sales(self.request.user):
            queryset = queryset.filter(operator=self.request.user)

        form = SaleFilterForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            if data.get("date_from"):
                start = timezone.make_aware(datetime.combine(data["date_from"], time.min))
                queryset = queryset.filter(created_at__gte=start)
            if data.get("date_to"):
                end = timezone.make_aware(datetime.combine(data["date_to"], time.max))
                queryset = queryset.filter(created_at__lte=end)
            if data.get("operator") and can_view_all_sales(self.request.user):
                queryset = queryset.filter(operator_id=data["operator"])
            if data.get("method"):
                queryset = queryset.filter(payments__method=data["method"])
            if data.get("status"):
                queryset = queryset.filter(status=data["status"])
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = SaleFilterForm(self.request.GET)
        context["operators"] = User.objects.filter(sales__isnull=False).distinct().order_by("username")
        context["can_view_operators"] = can_view_all_sales(self.request.user)
        return context


class SaleDetailView(SalesHistoryRequiredMixin, DetailView):
    model = Sale
    template_name = "sales/sale_detail.html"
    context_object_name = "sale"

    def get_queryset(self):
        return Sale.objects.select_related("operator", "canceled_by", "session").prefetch_related(
            "items__product", "payments"
        )

    def get_object(self, queryset=None):
        sale = super().get_object(queryset)
        if not can_view_sale(self.request.user, sale):
            raise PermissionDenied("Você não pode ver esta venda.")
        return sale

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_form"] = SaleCancelForm()
        context["can_cancel"] = (
            can_cancel_sale(self.request.user)
            and self.object.status == Sale.Status.COMPLETED
        )
        return context


class SaleReceiptView(SalesHistoryRequiredMixin, DetailView):
    model = Sale
    template_name = "sales/receipt.html"
    context_object_name = "sale"

    def get_queryset(self):
        return Sale.objects.select_related("operator", "canceled_by").prefetch_related(
            "items", "payments"
        )

    def get_object(self, queryset=None):
        sale = super().get_object(queryset)
        if not can_view_sale(self.request.user, sale):
            raise PermissionDenied("Você não pode ver esta venda.")
        return sale

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["autoprint"] = self.request.GET.get("autoprint") == "1"
        context.update(store_context())
        return context


class SalePrintView(SalesHistoryRequiredMixin, View):
    def post(self, request, pk):
        sale = get_object_or_404(
            Sale.objects.select_related("operator").prefetch_related("items", "payments"),
            pk=pk,
        )
        if not can_view_sale(request.user, sale):
            raise PermissionDenied("Você não pode imprimir esta venda.")
        result = print_sale_receipt(sale)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": result.ok,
                    "printed": result.ok,
                    "print_method": result.method,
                    "print_error": result.error,
                    "number": sale.number,
                }
            )
        if result.ok:
            messages.success(request, f"Comprovante da venda {sale.number} enviado.")
        else:
            messages.error(request, result.error or "Não foi possível imprimir.")
        return redirect("sales:detail", pk=sale.pk)


class SaleCancelView(CancelSaleRequiredMixin, View):
    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk)
        form = SaleCancelForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Informe o motivo do cancelamento.")
            return redirect("sales:detail", pk=sale.pk)
        try:
            cancel_sale(sale=sale, user=request.user, reason=form.cleaned_data["reason"])
        except DomainError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Venda {sale.number} cancelada. Estoque devolvido.")
        return redirect("sales:detail", pk=sale.pk)
