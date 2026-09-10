from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.core.permissions import GROUP_MANAGER
from apps.core.test_utils import make_product, make_user, open_test_session
from apps.dashboard.services import dashboard_metrics
from apps.sales.models import Payment
from apps.sales.services import cancel_sale, complete_sale


class DashboardTests(TestCase):
    def setUp(self):
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.product = make_product(price="10.00", stock_qty=10)
        self.session = open_test_session(self.gerente)

    def test_canceled_sale_out_of_revenue(self):
        kept = complete_sale(
            operator=self.gerente,
            items=[{"product_id": self.product.id, "quantity": 1}],
            payment_method=Payment.Method.PIX,
        )
        canceled = complete_sale(
            operator=self.gerente,
            items=[{"product_id": self.product.id, "quantity": 2}],
            payment_method=Payment.Method.PIX,
        )
        cancel_sale(sale=canceled, user=self.gerente, reason="Teste dashboard")
        metrics = dashboard_metrics()
        self.assertEqual(metrics["sales_count_today"], 1)
        self.assertEqual(metrics["revenue_today"], Decimal("10.00"))
        self.assertEqual(metrics["average_ticket_today"], Decimal("10.00"))
        self.assertEqual(kept.status, "COMPLETED")

    def test_dashboard_requires_manager(self):
        self.client.force_login(self.gerente)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Faturamento")
