from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class CashSession(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        CLOSED = "CLOSED", "Fechado"

    number = models.CharField("Número", max_length=20, unique=True, blank=True)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Operador",
        on_delete=models.PROTECT,
        related_name="cash_sessions",
    )
    status = models.CharField(
        "Status",
        max_length=12,
        choices=Status.choices,
        default=Status.OPEN,
    )
    opening_amount = models.DecimalField(
        "Fundo de caixa",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField("Fechado em", null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Fechado por",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="closed_cash_sessions",
    )
    sales_count = models.PositiveIntegerField("Vendas", default=0)
    canceled_count = models.PositiveIntegerField("Canceladas", default=0)
    sales_total = models.DecimalField(
        "Total das vendas",
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    expected_cash = models.DecimalField(
        "Dinheiro esperado",
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    expected_pix = models.DecimalField("PIX esperado", max_digits=12, decimal_places=2, default=0)
    expected_debit = models.DecimalField(
        "Débito esperado", max_digits=12, decimal_places=2, default=0
    )
    expected_credit = models.DecimalField(
        "Crédito esperado", max_digits=12, decimal_places=2, default=0
    )
    counted_cash = models.DecimalField(
        "Dinheiro conferido", max_digits=12, decimal_places=2, null=True, blank=True
    )
    counted_pix = models.DecimalField(
        "PIX conferido", max_digits=12, decimal_places=2, null=True, blank=True
    )
    counted_debit = models.DecimalField(
        "Débito conferido", max_digits=12, decimal_places=2, null=True, blank=True
    )
    counted_credit = models.DecimalField(
        "Crédito conferido", max_digits=12, decimal_places=2, null=True, blank=True
    )
    difference_cash = models.DecimalField(
        "Diferença dinheiro", max_digits=12, decimal_places=2, default=0
    )
    difference_pix = models.DecimalField(
        "Diferença PIX", max_digits=12, decimal_places=2, default=0
    )
    difference_debit = models.DecimalField(
        "Diferença débito", max_digits=12, decimal_places=2, default=0
    )
    difference_credit = models.DecimalField(
        "Diferença crédito", max_digits=12, decimal_places=2, default=0
    )
    notes = models.CharField("Observação", max_length=240, blank=True)

    class Meta:
        verbose_name = "Caixa"
        verbose_name_plural = "Caixas"
        ordering = ["-opened_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["operator"],
                condition=models.Q(status="OPEN"),
                name="unique_open_cash_session_per_operator",
            )
        ]

    def __str__(self):
        return f"Caixa {self.number or self.pk}"


class Sale(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberta"
        COMPLETED = "COMPLETED", "Concluída"
        CANCELED = "CANCELED", "Cancelada"

    number = models.CharField("Número", max_length=20, unique=True, blank=True)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Operador",
        on_delete=models.PROTECT,
        related_name="sales",
    )
    session = models.ForeignKey(
        CashSession,
        verbose_name="Caixa",
        on_delete=models.PROTECT,
        related_name="sales",
        null=True,
        blank=True,
    )
    status = models.CharField(
        "Status",
        max_length=12,
        choices=Status.choices,
        default=Status.OPEN,
    )
    subtotal = models.DecimalField(
        "Subtotal",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    discount = models.DecimalField(
        "Desconto",
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    total = models.DecimalField(
        "Total",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField("Finalizada em", null=True, blank=True)
    canceled_at = models.DateTimeField("Cancelada em", null=True, blank=True)
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Cancelada por",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="canceled_sales",
    )
    cancel_reason = models.CharField("Motivo do cancelamento", max_length=240, blank=True)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Venda {self.number or self.pk}"

    @property
    def payment(self):
        return self.payments.first()


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        verbose_name="Venda",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Produto",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )
    product_name_snapshot = models.CharField("Nome no momento da venda", max_length=120)
    unit_price = models.DecimalField(
        "Preço unitário",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    quantity = models.PositiveIntegerField("Quantidade", validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(
        "Subtotal",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = "Item da venda"
        verbose_name_plural = "Itens da venda"

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot}"


class Payment(models.Model):
    class Method(models.TextChoices):
        DINHEIRO = "DINHEIRO", "Dinheiro"
        PIX = "PIX", "PIX"
        DEBITO = "DEBITO", "Cartão de débito"
        CREDITO = "CREDITO", "Cartão de crédito"

    sale = models.ForeignKey(
        Sale,
        verbose_name="Venda",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    method = models.CharField("Forma", max_length=12, choices=Method.choices)
    amount = models.DecimalField(
        "Valor",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    amount_received = models.DecimalField(
        "Valor recebido",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    change = models.DecimalField(
        "Troco",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"

    def __str__(self):
        return f"{self.get_method_display()} {self.amount}"
