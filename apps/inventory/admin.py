from django.contrib import admin

from apps.inventory.models import Stock, StockMovement


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "minimum_quantity", "updated_at")
    search_fields = ("product__name", "product__sku")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "product",
        "type",
        "quantity",
        "quantity_before",
        "quantity_after",
        "user",
    )
    list_filter = ("type",)
    search_fields = ("product__name", "reason")
