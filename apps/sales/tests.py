import json
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.exceptions import DomainError
from apps.core.permissions import GROUP_ADMIN, GROUP_CASHIER, GROUP_MANAGER
from apps.core.test_utils import make_product, make_user, open_test_session
from apps.inventory.models import StockMovement
from apps.sales.cash import close_cash_session
from apps.sales.models import CashSession, Payment, Sale
from apps.sales.receipt_print import build_receipt_text, print_sale_receipt
from apps.sales.services import cancel_sale, complete_sale


class SaleServiceTests(TestCase):
    def setUp(self):
        self.caixa = make_user("caixa1", GROUP_CASHIER)
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.product = make_product(price="12.50", stock_qty=5)
        self.session = open_test_session(self.caixa)

    def test_complete_sale_decrements_stock(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 2}],
            payment_method=Payment.Method.PIX,
        )
        self.assertEqual(sale.status, Sale.Status.COMPLETED)
        self.assertEqual(sale.subtotal, Decimal("25.00"))
        self.assertEqual(sale.total, Decimal("25.00"))
        self.product.stock.refresh_from_db()
        self.assertEqual(self.product.stock.quantity, 3)
        move = StockMovement.objects.get(sale=sale, type=StockMovement.Type.SALE)
        self.assertEqual(move.quantity_before, 5)
        self.assertEqual(move.quantity_after, 3)
        self.assertEqual(sale.items.get().product_name_snapshot, self.product.name)
        self.assertEqual(sale.items.get().unit_price, Decimal("12.50"))

    def test_backend_recalculates_total_from_current_price(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 3}],
            payment_method=Payment.Method.DEBITO,
        )
        self.assertEqual(sale.total, Decimal("37.50"))

    def test_insufficient_stock_blocks_sale(self):
        with self.assertRaises(DomainError) as ctx:
            complete_sale(
                operator=self.caixa,
                items=[{"product_id": self.product.id, "quantity": 9}],
                payment_method=Payment.Method.PIX,
            )
        self.assertIn("Estoque insuficiente", str(ctx.exception))
        self.product.stock.refresh_from_db()
        self.assertEqual(self.product.stock.quantity, 5)
        self.assertEqual(Sale.objects.count(), 0)

    def test_cash_payment_and_change(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.DINHEIRO,
            amount_received="20.00",
        )
        payment = sale.payment
        self.assertEqual(payment.amount, Decimal("12.50"))
        self.assertEqual(payment.amount_received, Decimal("20.00"))
        self.assertEqual(payment.change, Decimal("7.50"))

    def test_cash_below_total_is_rejected(self):
        with self.assertRaises(DomainError):
            complete_sale(
                operator=self.caixa,
                items=[{"product_id": self.product.id, "quantity": 1}],
                payment_method=Payment.Method.DINHEIRO,
                amount_received="10.00",
            )

    def test_cancel_returns_stock(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 2}],
            payment_method=Payment.Method.CREDITO,
        )
        cancel_sale(sale=sale, user=self.gerente, reason="Cliente desistiu DEMO")
        sale.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.CANCELED)
        self.assertEqual(sale.cancel_reason, "Cliente desistiu DEMO")
        self.product.stock.refresh_from_db()
        self.assertEqual(self.product.stock.quantity, 5)
        self.assertTrue(
            StockMovement.objects.filter(
                sale=sale, type=StockMovement.Type.SALE_REVERSAL
            ).exists()
        )

    def test_canceled_sale_cannot_cancel_again(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        cancel_sale(sale=sale, user=self.gerente, reason="Erro DEMO")
        with self.assertRaises(DomainError):
            cancel_sale(sale=sale, user=self.gerente, reason="De novo")


class SaleViewTests(TestCase):
    def setUp(self):
        self.caixa = make_user("caixa1", GROUP_CASHIER)
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.admin = make_user("admin1", GROUP_ADMIN)
        self.product = make_product(price="10.00", stock_qty=4)
        self.session = open_test_session(self.caixa)

    def test_pdv_checkout_post(self):
        self.client.force_login(self.caixa)
        response = self.client.post(
            reverse("sales:pdv_checkout"),
            data=json.dumps(
                {
                    "items": [{"product_id": self.product.id, "quantity": 1}],
                    "payment_method": "PIX",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["number"])
        sale = Sale.objects.get(number=payload["number"])
        self.assertEqual(payload["print_url"], reverse("sales:receipt", args=[sale.pk]))
        self.assertTrue(payload["printed"])
        self.assertEqual(payload["print_method"], "terminal")
        self.assertEqual(payload["reprint_url"], reverse("sales:print", args=[sale.pk]))

    def test_receipt_prints_for_operator(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        self.client.force_login(self.caixa)
        response = self.client.get(reverse("sales:receipt", args=[sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sale.number)
        self.assertContains(response, "Cupom não fiscal")
        self.assertContains(response, "Pastel da TATI")
        self.assertNotContains(response, "afterprint")

    def test_receipt_autoprint_triggers_print(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        self.client.force_login(self.caixa)
        response = self.client.get(
            reverse("sales:receipt", args=[sale.pk]),
            {"autoprint": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "afterprint")
        self.assertContains(response, "is-autoprint")

    def test_caixa_cannot_print_other_operator_sale(self):
        other = make_user("caixa2", GROUP_CASHIER)
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        self.client.force_login(other)
        response = self.client.get(reverse("sales:receipt", args=[sale.pk]))
        self.assertEqual(response.status_code, 403)

    def test_canceled_receipt_shows_stamp(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        cancel_sale(sale=sale, user=self.gerente, reason="Erro DEMO")
        self.client.force_login(self.gerente)
        response = self.client.get(reverse("sales:receipt", args=[sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CANCELADA")

    def test_caixa_cannot_cancel(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        self.client.force_login(self.caixa)
        response = self.client.post(
            reverse("sales:cancel", args=[sale.pk]),
            {"reason": "Tentativa do caixa"},
        )
        self.assertEqual(response.status_code, 403)
        sale.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.COMPLETED)

    def test_gerente_can_cancel_via_post(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        self.client.force_login(self.gerente)
        response = self.client.post(
            reverse("sales:cancel", args=[sale.pk]),
            {"reason": "Erro de lançamento"},
        )
        self.assertRedirects(response, reverse("sales:detail", args=[sale.pk]))
        sale.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.CANCELED)

    def test_reprint_post_redirects(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        self.client.force_login(self.caixa)
        response = self.client.post(reverse("sales:print", args=[sale.pk]))
        self.assertRedirects(response, reverse("sales:detail", args=[sale.pk]))

    def test_pdv_redirects_without_open_cash(self):
        other = make_user("caixa3", GROUP_CASHIER)
        self.client.force_login(other)
        response = self.client.get(reverse("sales:pdv"))
        self.assertRedirects(response, reverse("sales:cash_open"))


class ReceiptPrintTests(TestCase):
    def setUp(self):
        self.caixa = make_user("caixa1", GROUP_CASHIER)
        self.product = make_product(price="10.00", stock_qty=4)
        self.session = open_test_session(self.caixa)

    def test_receipt_text_has_totals(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 2}],
            payment_method=Payment.Method.PIX,
        )
        text = build_receipt_text(sale)
        self.assertIn(sale.number, text)
        self.assertIn("TOTAL", text)
        self.assertIn("PASTEL DA TATI", text)
        self.assertIn("PIX", text)

    def test_print_writes_spool(self):
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.DINHEIRO,
            amount_received="20.00",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(
                THERMAL_SPOOL_DIR=tmp,
                THERMAL_PRINTER_HOST="",
                THERMAL_AGENT_URL="",
            ):
                result = print_sale_receipt(sale)
            latest = Path(tmp) / "latest.txt"
            self.assertTrue(result.ok)
            self.assertEqual(result.method, "terminal")
            self.assertTrue(latest.exists())
            self.assertIn(sale.number, latest.read_text(encoding="utf-8"))


class CashSessionTests(TestCase):
    def setUp(self):
        self.caixa = make_user("caixa1", GROUP_CASHIER)
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.product = make_product(price="10.00", stock_qty=10)

    def test_sale_blocked_without_open_cash(self):
        with self.assertRaises(DomainError) as ctx:
            complete_sale(
                operator=self.caixa,
                items=[{"product_id": self.product.id, "quantity": 1}],
                payment_method=Payment.Method.PIX,
            )
        self.assertIn("Abra o caixa", str(ctx.exception))

    def test_open_and_close_with_conference(self):
        session = open_test_session(self.caixa, "50.00")
        complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.DINHEIRO,
            amount_received="20.00",
        )
        complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        closed = close_cash_session(
            session=session,
            user=self.caixa,
            counted_cash="60,00",
            notes="",
        )
        self.assertEqual(closed.status, CashSession.Status.CLOSED)
        self.assertEqual(closed.expected_cash, Decimal("60.00"))
        self.assertEqual(closed.counted_cash, Decimal("60.00"))
        self.assertEqual(closed.difference_cash, Decimal("0.00"))
        self.assertEqual(closed.expected_pix, Decimal("10.00"))
        self.assertEqual(closed.sales_count, 2)

    def test_close_quebra_requires_note(self):
        session = open_test_session(self.caixa, "10.00")
        complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.DINHEIRO,
            amount_received="10.00",
        )
        with self.assertRaises(DomainError):
            close_cash_session(
                session=session,
                user=self.caixa,
                counted_cash="15.00",
                notes="",
            )
        closed = close_cash_session(
            session=session,
            user=self.caixa,
            counted_cash="15.00",
            notes="Quebra DEMO",
        )
        self.assertEqual(closed.expected_cash, Decimal("20.00"))
        self.assertEqual(closed.difference_cash, Decimal("-5.00"))
        self.assertEqual(closed.notes, "Quebra DEMO")

    def test_cannot_cancel_after_close(self):
        session = open_test_session(self.caixa, "0")
        sale = complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        close_cash_session(session=session, user=self.caixa, counted_cash="0")
        with self.assertRaises(DomainError) as ctx:
            cancel_sale(sale=sale, user=self.gerente, reason="Tarde DEMO")
        self.assertIn("caixa já fechado", str(ctx.exception))

    def test_open_close_views_and_print(self):
        self.client.force_login(self.caixa)
        response = self.client.post(
            reverse("sales:cash_open"),
            {"opening_amount": "30,00"},
        )
        self.assertRedirects(response, reverse("sales:pdv"))
        session = CashSession.objects.get(operator=self.caixa)
        self.assertEqual(session.opening_amount, Decimal("30.00"))
        complete_sale(
            operator=self.caixa,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        response = self.client.post(
            reverse("sales:cash_close"),
            {"counted_cash": "30,00"},
        )
        self.assertRedirects(response, reverse("sales:cash_detail", args=[session.pk]))
        session.refresh_from_db()
        self.assertEqual(session.status, CashSession.Status.CLOSED)
        response = self.client.post(
            reverse("sales:cash_print", args=[session.pk]),
            {"tipo": "fechamento"},
        )
        self.assertRedirects(response, reverse("sales:cash_detail", args=[session.pk]))
