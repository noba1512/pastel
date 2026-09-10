from django.test import TestCase
from django.urls import reverse

from apps.core.permissions import GROUP_CASHIER, GROUP_MANAGER
from apps.core.test_utils import make_product, make_user
from apps.inventory.models import StockMovement


class StockTests(TestCase):
    def setUp(self):
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.caixa = make_user("caixa1", GROUP_CASHIER)
        self.product = make_product(stock_qty=0)

    def test_stock_entry(self):
        self.client.force_login(self.gerente)
        response = self.client.post(
            reverse("inventory:stock_entry"),
            {
                "product": self.product.pk,
                "quantity": 15,
                "reason": "Compra DEMO",
            },
        )
        self.assertRedirects(response, reverse("inventory:stock_list"))
        self.product.stock.refresh_from_db()
        self.assertEqual(self.product.stock.quantity, 15)
        move = StockMovement.objects.get(product=self.product)
        self.assertEqual(move.type, StockMovement.Type.ENTRY)
        self.assertEqual(move.quantity_before, 0)
        self.assertEqual(move.quantity_after, 15)

    def test_caixa_cannot_adjust_stock(self):
        self.client.force_login(self.caixa)
        response = self.client.post(
            reverse("inventory:stock_entry"),
            {"product": self.product.pk, "quantity": 1, "reason": "x"},
        )
        self.assertEqual(response.status_code, 403)
        self.product.stock.refresh_from_db()
        self.assertEqual(self.product.stock.quantity, 0)
