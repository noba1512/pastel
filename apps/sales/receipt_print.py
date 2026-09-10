import logging
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.core.store import store_context
from apps.core.templatetags.pastel_tags import brl, datetime_br, payment_label
from apps.sales.cash import difference_kind
from apps.sales.models import CashSession, Sale

logger = logging.getLogger(__name__)

WIDTH = 48


@dataclass
class PrintResult:
    ok: bool
    method: str
    error: str = ""


def _center(text, width=WIDTH):
    text = text[:width]
    pad = max(0, width - len(text))
    left = pad // 2
    return (" " * left) + text


def _row(left, right, width=WIDTH):
    left = str(left)
    right = str(right)
    space = width - len(right)
    if space <= 1:
        return (left[:width] + "\n" + right.rjust(width))
    if len(left) > space - 1:
        left = left[: space - 1]
    return f"{left}{right.rjust(width - len(left))}"


def _hr():
    return "-" * WIDTH


def build_receipt_text(sale):
    store = store_context()
    payment = sale.payment
    lines = [
        _center(store["store_name"].upper()),
    ]
    if store["store_address"]:
        lines.append(_center(store["store_address"]))
    if store["store_document"]:
        lines.append(_center(store["store_document"]))
    if store["store_phone"]:
        lines.append(_center(store["store_phone"]))
    lines += [
        _hr(),
        _center("CUPOM NAO FISCAL"),
        _center("Nao substitui documento fiscal"),
        _hr(),
        _row(f"No {sale.number}", datetime_br(sale.created_at)),
        f"Operador: {sale.operator.username}",
    ]
    if sale.status == Sale.Status.CANCELED:
        lines.append(_center("*** CANCELADA ***"))
    lines.append(_hr())
    for item in sale.items.all():
        lines.append(f"{item.quantity}x {item.product_name_snapshot}"[:WIDTH])
        lines.append(_row(f"  {brl(item.unit_price)} un.", brl(item.subtotal)))
    lines.append(_hr())
    lines.append(_row("Subtotal", brl(sale.subtotal)))
    if sale.discount:
        lines.append(_row("Desconto", f"- {brl(sale.discount)}"))
    lines.append(_row("TOTAL", brl(sale.total)))
    lines.append(_hr())
    if payment:
        lines.append(_row(payment_label(payment.method), brl(payment.amount)))
        if payment.amount_received is not None:
            lines.append(_row("Recebido", brl(payment.amount_received)))
            lines.append(_row("Troco", brl(payment.change)))
    lines.append(_hr())
    lines.append(_center(store["store_footer"]))
    lines.append("")
    return "\n".join(lines)


def _escpos_payload(text):
    payload = bytearray()
    payload += b"\x1b@"
    payload += b"\x1bt\x02"
    payload += b"\x1ba\x00"
    payload += text.encode("cp850", errors="replace")
    payload += b"\n\n\n"
    payload += b"\x1dVA\x03"
    return bytes(payload)


def _write_spool(spool_key, text, payload):
    folder = _spool_dir()
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}-{spool_key}"
    (folder / f"{base}.txt").write_text(text, encoding="utf-8")
    (folder / f"{base}.bin").write_bytes(payload)
    (folder / "latest.txt").write_text(text, encoding="utf-8")
    (folder / "latest.bin").write_bytes(payload)
    return folder / f"{base}.txt"


def _spool_dir():
    path = Path(settings.THERMAL_SPOOL_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _send_tcp(payload):
    host = (settings.THERMAL_PRINTER_HOST or "").strip()
    if not host:
        return False, ""
    port = int(settings.THERMAL_PRINTER_PORT)
    with socket.create_connection((host, port), timeout=1.5) as sock:
        sock.sendall(payload)
    return True, "tcp"


def _send_agent(payload):
    url = (settings.THERMAL_AGENT_URL or "").strip()
    if not url:
        return False, ""
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/octet-stream"},
    )
    with urllib.request.urlopen(req, timeout=1.5) as response:
        if response.status >= 400:
            raise RuntimeError(f"Agente de impressão HTTP {response.status}")
    return True, "agent"


def dispatch_receipt(text, spool_key, title):
    payload = _escpos_payload(text)
    banner = (
        f"\n========== {title} ==========\n"
        f"{text}"
        f"====================================\n"
    )
    print(banner, flush=True)
    logger.info("%s enviado ao terminal.", title)

    try:
        _write_spool(spool_key, text, payload)
    except OSError as exc:
        logger.warning("Falha ao gravar spool %s: %s", spool_key, exc)

    errors = []
    for sender in (_send_tcp, _send_agent):
        try:
            sent, method = sender(payload)
            if sent:
                return PrintResult(ok=True, method=method)
        except (OSError, TimeoutError, urllib.error.URLError, RuntimeError) as exc:
            errors.append(str(exc))

    return PrintResult(ok=True, method="terminal", error="; ".join(errors))


def _store_header():
    store = store_context()
    lines = [_center(store["store_name"].upper())]
    if store["store_address"]:
        lines.append(_center(store["store_address"]))
    if store["store_document"]:
        lines.append(_center(store["store_document"]))
    if store["store_phone"]:
        lines.append(_center(store["store_phone"]))
    return lines, store


def _diff_line(label, expected, counted, diff):
    kind = difference_kind(diff)
    tag = {"ok": "OK", "sobra": "SOBRA", "quebra": "QUEBRA"}[kind]
    lines = [
        _row(f"{label} sist.", brl(expected)),
        _row(f"{label} cont.", brl(counted)),
        _row(f"Dif. {label} {tag}", brl(diff)),
    ]
    return lines


def build_cash_open_text(session):
    lines, store = _store_header()
    lines += [
        _hr(),
        _center("ABERTURA DE CAIXA"),
        _center("Cupom nao fiscal"),
        _hr(),
        _row(session.number, datetime_br(session.opened_at)),
        f"Operador: {session.operator.username}",
        _hr(),
        _row("Fundo de caixa", brl(session.opening_amount)),
        _hr(),
        _center(store["store_footer"]),
        "",
    ]
    return "\n".join(lines)


def build_cash_close_text(session):
    lines, store = _store_header()
    kind = difference_kind(session.difference_cash)
    tag = {"ok": "CONFERENCIA OK", "sobra": "SOBRA EM DINHEIRO", "quebra": "QUEBRA EM DINHEIRO"}[kind]
    lines += [
        _hr(),
        _center("FECHAMENTO DE CAIXA"),
        _center("Cupom nao fiscal"),
        _hr(),
        _row(session.number, datetime_br(session.closed_at or session.opened_at)),
        f"Operador: {session.operator.username}",
        f"Fechado por: {session.closed_by.username if session.closed_by else '—'}",
        _row("Aberto", datetime_br(session.opened_at)),
        _row("Fechado", datetime_br(session.closed_at)),
        _hr(),
        _center("CONFERENCIA"),
        _row("Fundo de caixa", brl(session.opening_amount)),
        _row("Vendas dinheiro", brl(session.expected_cash - session.opening_amount)),
        *_diff_line("Dinheiro", session.expected_cash, session.counted_cash, session.difference_cash),
        _hr(),
        *_diff_line("PIX", session.expected_pix, session.counted_pix, session.difference_pix),
        *_diff_line("Debito", session.expected_debit, session.counted_debit, session.difference_debit),
        *_diff_line("Credito", session.expected_credit, session.counted_credit, session.difference_credit),
        _hr(),
        _row("Vendas", str(session.sales_count)),
        _row("Canceladas", str(session.canceled_count)),
        _row("TOTAL VENDAS", brl(session.sales_total)),
        _center(tag),
    ]
    if session.notes:
        lines.append(_hr())
        lines.append("Obs: " + session.notes)
    lines += [_hr(), _center(store["store_footer"]), ""]
    return "\n".join(lines)


def print_sale_receipt(sale):
    sale = (
        Sale.objects.select_related("operator")
        .prefetch_related("items", "payments")
        .get(pk=sale.pk)
    )
    return dispatch_receipt(build_receipt_text(sale), sale.number, f"CUPOM {sale.number}")


def print_cash_open_receipt(session):
    session = CashSession.objects.select_related("operator").get(pk=session.pk)
    return dispatch_receipt(
        build_cash_open_text(session),
        f"{session.number}-abertura",
        f"ABERTURA {session.number}",
    )


def print_cash_close_receipt(session):
    session = CashSession.objects.select_related("operator", "closed_by").get(pk=session.pk)
    return dispatch_receipt(
        build_cash_close_text(session),
        f"{session.number}-fechamento",
        f"FECHAMENTO {session.number}",
    )
