from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.core.exceptions import DomainError
from apps.core.permissions import can_view_all_sales
from apps.sales.models import CashSession, Payment, Sale
from apps.sales.services import money, parse_money_input

ZERO = Decimal("0.00")


def get_open_session(user):
    if not user or not user.is_authenticated:
        return None
    return CashSession.objects.filter(
        operator=user, status=CashSession.Status.OPEN
    ).first()


def can_view_session(user, session):
    if can_view_all_sales(user):
        return True
    return session.operator_id == user.id


def can_close_session(user, session):
    if session.status != CashSession.Status.OPEN:
        return False
    return can_view_session(user, session)


def session_totals(session):
    completed = session.sales.filter(status=Sale.Status.COMPLETED)
    canceled = session.sales.filter(status=Sale.Status.CANCELED)
    by_method = {
        Payment.Method.DINHEIRO: ZERO,
        Payment.Method.PIX: ZERO,
        Payment.Method.DEBITO: ZERO,
        Payment.Method.CREDITO: ZERO,
    }
    rows = (
        Payment.objects.filter(sale__session=session, sale__status=Sale.Status.COMPLETED)
        .values("method")
        .annotate(total=Sum("amount"))
    )
    for row in rows:
        by_method[row["method"]] = money(row["total"] or 0)
    cash_sales = by_method[Payment.Method.DINHEIRO]
    opening = money(session.opening_amount)
    sales_total = money(completed.aggregate(total=Sum("total"))["total"] or 0)
    return {
        "sales_count": completed.count(),
        "canceled_count": canceled.count(),
        "sales_total": sales_total,
        "by_method": by_method,
        "cash_sales": cash_sales,
        "expected_cash": money(opening + cash_sales),
        "expected_pix": by_method[Payment.Method.PIX],
        "expected_debit": by_method[Payment.Method.DEBITO],
        "expected_credit": by_method[Payment.Method.CREDITO],
    }


def difference_kind(diff):
    if diff == 0:
        return "ok"
    if diff > 0:
        return "sobra"
    return "quebra"


def _next_cash_number():
    last = (
        CashSession.objects.select_for_update()
        .exclude(number="")
        .order_by("-pk")
        .values_list("number", flat=True)
        .first()
    )
    if last and last.startswith("CX") and last[2:].isdigit():
        return f"CX{int(last[2:]) + 1:06d}"
    count = CashSession.objects.select_for_update().count()
    return f"CX{count + 1:06d}"


@transaction.atomic
def open_cash_session(*, operator, opening_amount):
    opening = parse_money_input(opening_amount) if not isinstance(opening_amount, Decimal) else money(opening_amount)
    if opening < 0:
        raise DomainError("Fundo de caixa inválido.")
    existing = (
        CashSession.objects.select_for_update()
        .filter(operator=operator, status=CashSession.Status.OPEN)
        .first()
    )
    if existing:
        raise DomainError("Você já tem um caixa aberto.")
    return CashSession.objects.create(
        number=_next_cash_number(),
        operator=operator,
        status=CashSession.Status.OPEN,
        opening_amount=opening,
    )


def _optional_counted(raw, expected):
    if raw is None or str(raw).strip() == "":
        return money(expected)
    return parse_money_input(raw)


@transaction.atomic
def close_cash_session(
    *,
    session,
    user,
    counted_cash,
    counted_pix="",
    counted_debit="",
    counted_credit="",
    notes="",
):
    session = CashSession.objects.select_for_update().get(pk=session.pk)
    if session.status != CashSession.Status.OPEN:
        raise DomainError("Este caixa já está fechado.")
    if not can_close_session(user, session):
        raise DomainError("Você não pode fechar este caixa.")

    totals = session_totals(session)
    cash = parse_money_input(counted_cash)
    pix = _optional_counted(counted_pix, totals["expected_pix"])
    debit = _optional_counted(counted_debit, totals["expected_debit"])
    credit = _optional_counted(counted_credit, totals["expected_credit"])
    notes = (notes or "").strip()

    diff_cash = money(cash - totals["expected_cash"])
    if diff_cash != 0 and not notes:
        raise DomainError("Informe o motivo da diferença no dinheiro.")

    session.status = CashSession.Status.CLOSED
    session.closed_at = timezone.now()
    session.closed_by = user
    session.sales_count = totals["sales_count"]
    session.canceled_count = totals["canceled_count"]
    session.sales_total = totals["sales_total"]
    session.expected_cash = totals["expected_cash"]
    session.expected_pix = totals["expected_pix"]
    session.expected_debit = totals["expected_debit"]
    session.expected_credit = totals["expected_credit"]
    session.counted_cash = cash
    session.counted_pix = pix
    session.counted_debit = debit
    session.counted_credit = credit
    session.difference_cash = diff_cash
    session.difference_pix = money(pix - totals["expected_pix"])
    session.difference_debit = money(debit - totals["expected_debit"])
    session.difference_credit = money(credit - totals["expected_credit"])
    session.notes = notes
    session.save()
    return session
