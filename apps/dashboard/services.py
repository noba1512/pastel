from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import F, Sum
from django.utils import timezone

from apps.inventory.models import Stock
from apps.sales.models import Sale, SaleItem


def _today_range():
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, time.min))
    end = timezone.make_aware(datetime.combine(today, time.max))
    return start, end


def dashboard_metrics():
    start, end = _today_range()
    today_sales = Sale.objects.filter(
        status=Sale.Status.COMPLETED,
        finished_at__range=(start, end),
    )
    revenue = today_sales.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
    count = today_sales.count()
    ticket = (
        (revenue / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if count
        else Decimal("0.00")
    )

    low_stock = (
        Stock.objects.select_related("product", "product__category")
        .filter(quantity__lte=F("minimum_quantity"))
        .order_by("quantity", "product__name")[:8]
    )

    top_products = (
        SaleItem.objects.filter(sale__status=Sale.Status.COMPLETED)
        .values("product_name_snapshot")
        .annotate(qty=Sum("quantity"), amount=Sum("subtotal"))
        .order_by("-qty")[:5]
    )

    latest_sales = (
        Sale.objects.filter(status=Sale.Status.COMPLETED)
        .select_related("operator")
        .prefetch_related("payments")[:8]
    )

    return {
        "revenue_today": revenue,
        "sales_count_today": count,
        "average_ticket_today": ticket,
        "low_stock": low_stock,
        "top_products": top_products,
        "latest_sales": latest_sales,
        "has_data": count > 0 or low_stock.exists() or bool(top_products),
    }
