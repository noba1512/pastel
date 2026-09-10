from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField("Nome", max_length=80)
    active = models.BooleanField("Ativa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("Nome", max_length=120)
    sku = models.CharField("SKU", max_length=40, unique=True)
    category = models.ForeignKey(
        Category,
        verbose_name="Categoria",
        on_delete=models.PROTECT,
        related_name="products",
    )
    sale_price = models.DecimalField(
        "Preço de venda",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"
