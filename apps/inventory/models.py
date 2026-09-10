from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Stock(models.Model):
    product = models.OneToOneField(
        "catalog.Product",
        verbose_name="Produto",
        on_delete=models.CASCADE,
        related_name="stock",
    )
    quantity = models.PositiveIntegerField("Quantidade", default=0)
    minimum_quantity = models.PositiveIntegerField("Estoque mínimo", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estoque"
        verbose_name_plural = "Estoques"
        ordering = ["product__name"]

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"

    @property
    def situation(self):
        if self.quantity <= 0:
            return "out"
        if self.quantity <= self.minimum_quantity:
            return "low"
        return "ok"

    @property
    def situation_label(self):
        return {
            "out": "Sem estoque",
            "low": "Baixo",
            "ok": "Normal",
        }[self.situation]


class StockMovement(models.Model):
    class Type(models.TextChoices):
        ENTRY = "ENTRY", "Entrada"
        SALE = "SALE", "Venda"
        ADJUSTMENT_IN = "ADJUSTMENT_IN", "Ajuste de entrada"
        ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Ajuste de saída"
        SALE_REVERSAL = "SALE_REVERSAL", "Estorno de venda"

    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Produto",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    type = models.CharField("Tipo", max_length=20, choices=Type.choices)
    quantity = models.PositiveIntegerField("Quantidade", validators=[MinValueValidator(1)])
    quantity_before = models.PositiveIntegerField("Quantidade anterior")
    quantity_after = models.PositiveIntegerField("Quantidade posterior")
    reason = models.CharField("Motivo", max_length=200, blank=True)
    sale = models.ForeignKey(
        "sales.Sale",
        verbose_name="Venda",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuário",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} {self.product} ({self.quantity})"
