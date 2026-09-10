from decimal import Decimal, InvalidOperation

from django import template
from django.utils import timezone

register = template.Library()


def _as_decimal(value):
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


@register.filter
def brl(value):
    amount = _as_decimal(value)
    if amount is None:
        return "—"
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


@register.filter
def date_br(value):
    if not value:
        return "—"
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%d/%m/%Y")


@register.filter
def datetime_br(value):
    if not value:
        return "—"
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%d/%m/%Y %H:%M")


@register.filter
def payment_label(value):
    labels = {
        "DINHEIRO": "Dinheiro",
        "PIX": "PIX",
        "DEBITO": "Cartão de débito",
        "CREDITO": "Cartão de crédito",
    }
    return labels.get(value, value or "—")


@register.filter
def sale_status_label(value):
    labels = {
        "OPEN": "Aberta",
        "COMPLETED": "Concluída",
        "CANCELED": "Cancelada",
    }
    return labels.get(value, value or "—")


@register.filter
def cash_status_label(value):
    labels = {
        "OPEN": "Aberto",
        "CLOSED": "Fechado",
    }
    return labels.get(value, value or "—")


@register.filter
def difference_label(value):
    amount = _as_decimal(value)
    if amount is None or amount == 0:
        return ""
    return "Sobra" if amount > 0 else "Quebra"
