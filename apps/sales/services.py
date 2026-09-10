from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Product
from apps.core.exceptions import DomainError
from apps.core.permissions import can_apply_discount
from apps.inventory.models import Stock, StockMovement
from apps.sales.models import CashSession, Payment, Sale, SaleItem

TWOPLACES = Decimal("0.01")


def money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise DomainError("Valor monetário inválido.") from exc
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def parse_money_input(raw):
    if raw is None or str(raw).strip() == "":
        raise DomainError("Valor monetário inválido.")
    text = str(raw).strip().replace("R$", "").replace("\xa0", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    return money(text)


def _merge_items(raw_items):
    merged = defaultdict(int)
    for item in raw_items:
        try:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError("Itens do pedido inválidos.") from exc
        if quantity <= 0:
            raise DomainError("A quantidade de cada item deve ser maior que zero.")
        merged[product_id] += quantity
    if not merged:
        raise DomainError("O pedido não possui itens.")
    return merged


def _next_sale_number():
    last = (
        Sale.objects.select_for_update()
        .exclude(number="")
        .order_by("-pk")
        .values_list("number", flat=True)
        .first()
    )
    if last and last.isdigit():
        return f"{int(last) + 1:06d}"
    count = Sale.objects.select_for_update().count()
    return f"{count + 1:06d}"


@transaction.atomic
def complete_sale(*, operator, items, payment_method, amount_received=None, discount=0):
    if payment_method not in Payment.Method.values:
        raise DomainError("Forma de pagamento inválida.")

    discount = money(discount or 0)
    if discount < 0:
        raise DomainError("Desconto inválido.")
    if discount > 0 and not can_apply_discount(operator):
        raise DomainError("Você não tem permissão para aplicar desconto.")

    merged = _merge_items(items)
    product_ids = list(merged.keys())

    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(pk__in=product_ids)
    }
    stocks = {
        stock.product_id: stock
        for stock in Stock.objects.select_for_update().filter(product_id__in=product_ids)
    }

    prepared = []
    subtotal = Decimal("0.00")
    for product_id, quantity in merged.items():
        product = products.get(product_id)
        if product is None:
            raise DomainError("Um dos produtos do pedido não foi encontrado.")
        if not product.active:
            raise DomainError(f"{product.name} está inativo e não pode ser vendido.")

        stock = stocks.get(product_id)
        if stock is None:
            raise DomainError(f"{product.name} não possui estoque cadastrado.")
        if stock.quantity < quantity:
            raise DomainError(
                f"Estoque insuficiente para {product.name}. "
                f"Disponível: {stock.quantity}."
            )

        unit_price = money(product.sale_price)
        line_subtotal = money(unit_price * quantity)
        subtotal += line_subtotal
        prepared.append(
            {
                "product": product,
                "stock": stock,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": line_subtotal,
            }
        )

    subtotal = money(subtotal)
    if discount > subtotal:
        raise DomainError("O desconto não pode ser maior que o subtotal.")
    total = money(subtotal - discount)

    received = None
    change = None
    if payment_method == Payment.Method.DINHEIRO:
        if amount_received is None or amount_received == "":
            raise DomainError("Informe o valor recebido em dinheiro.")
        received = money(amount_received)
        if received < total:
            raise DomainError("Valor recebido menor que o total. Não é possível finalizar.")
        change = money(received - total)

    session = (
        CashSession.objects.select_for_update()
        .filter(operator=operator, status=CashSession.Status.OPEN)
        .first()
    )
    if session is None:
        raise DomainError("Abra o caixa antes de vender.")

    now = timezone.now()
    sale = Sale.objects.create(
        number=_next_sale_number(),
        operator=operator,
        session=session,
        status=Sale.Status.COMPLETED,
        subtotal=subtotal,
        discount=discount,
        total=total,
        finished_at=now,
    )

    for line in prepared:
        SaleItem.objects.create(
            sale=sale,
            product=line["product"],
            product_name_snapshot=line["product"].name,
            unit_price=line["unit_price"],
            quantity=line["quantity"],
            subtotal=line["subtotal"],
        )
        stock = line["stock"]
        before = stock.quantity
        stock.quantity = before - line["quantity"]
        stock.save(update_fields=["quantity", "updated_at"])
        StockMovement.objects.create(
            product=line["product"],
            type=StockMovement.Type.SALE,
            quantity=line["quantity"],
            quantity_before=before,
            quantity_after=stock.quantity,
            reason=f"Venda {sale.number}",
            sale=sale,
            user=operator,
        )

    Payment.objects.create(
        sale=sale,
        method=payment_method,
        amount=total,
        amount_received=received,
        change=change,
    )
    return sale


@transaction.atomic
def cancel_sale(*, sale, user, reason):
    sale = Sale.objects.select_for_update().get(pk=sale.pk)
    if sale.status == Sale.Status.CANCELED:
        raise DomainError("Esta venda já foi cancelada.")
    if sale.status != Sale.Status.COMPLETED:
        raise DomainError("Só é possível cancelar uma venda concluída.")
    if sale.session_id:
        session = CashSession.objects.select_for_update().get(pk=sale.session_id)
        if session.status == CashSession.Status.CLOSED:
            raise DomainError("Não é possível cancelar venda de caixa já fechado.")
    if not reason or not str(reason).strip():
        raise DomainError("Informe o motivo do cancelamento.")

    items = list(sale.items.select_related("product"))
    product_ids = [item.product_id for item in items]
    stocks = {
        stock.product_id: stock
        for stock in Stock.objects.select_for_update().filter(product_id__in=product_ids)
    }

    for item in items:
        stock = stocks.get(item.product_id)
        if stock is None:
            raise DomainError(f"Estoque não encontrado para {item.product_name_snapshot}.")
        before = stock.quantity
        stock.quantity = before + item.quantity
        stock.save(update_fields=["quantity", "updated_at"])
        StockMovement.objects.create(
            product=item.product,
            type=StockMovement.Type.SALE_REVERSAL,
            quantity=item.quantity,
            quantity_before=before,
            quantity_after=stock.quantity,
            reason=f"Cancelamento da venda {sale.number}",
            sale=sale,
            user=user,
        )

    sale.status = Sale.Status.CANCELED
    sale.canceled_at = timezone.now()
    sale.canceled_by = user
    sale.cancel_reason = str(reason).strip()
    sale.save(
        update_fields=["status", "canceled_at", "canceled_by", "cancel_reason"]
    )
    return sale
