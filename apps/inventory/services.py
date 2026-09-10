from django.db import transaction

from apps.core.exceptions import DomainError
from apps.inventory.models import Stock, StockMovement


@transaction.atomic
def register_entry(*, product, quantity, user, reason=""):
    quantity = int(quantity)
    if quantity <= 0:
        raise DomainError("A quantidade de entrada deve ser maior que zero.")

    stock = Stock.objects.select_for_update().get(product=product)
    before = stock.quantity
    stock.quantity = before + quantity
    stock.save(update_fields=["quantity", "updated_at"])

    return StockMovement.objects.create(
        product=product,
        type=StockMovement.Type.ENTRY,
        quantity=quantity,
        quantity_before=before,
        quantity_after=stock.quantity,
        reason=reason or "Entrada de estoque",
        user=user,
    )


@transaction.atomic
def register_adjustment(*, product, quantity, user, reason, increase):
    quantity = int(quantity)
    if quantity <= 0:
        raise DomainError("A quantidade do ajuste deve ser maior que zero.")
    if not reason or not reason.strip():
        raise DomainError("Informe o motivo do ajuste.")

    stock = Stock.objects.select_for_update().get(product=product)
    before = stock.quantity

    if increase:
        after = before + quantity
        movement_type = StockMovement.Type.ADJUSTMENT_IN
    else:
        if before < quantity:
            raise DomainError(
                f"Não é possível reduzir {quantity} unidade(s). "
                f"Estoque atual: {before}."
            )
        after = before - quantity
        movement_type = StockMovement.Type.ADJUSTMENT_OUT

    stock.quantity = after
    stock.save(update_fields=["quantity", "updated_at"])

    return StockMovement.objects.create(
        product=product,
        type=movement_type,
        quantity=quantity,
        quantity_before=before,
        quantity_after=after,
        reason=reason.strip(),
        user=user,
    )


def ensure_stock(product, minimum_quantity=0):
    stock, _created = Stock.objects.get_or_create(
        product=product,
        defaults={"quantity": 0, "minimum_quantity": minimum_quantity},
    )
    return stock
