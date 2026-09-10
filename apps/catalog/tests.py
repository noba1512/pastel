from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.core.permissions import GROUP_MANAGER
from apps.core.test_utils import make_user


class ProductTests(TestCase):
    def setUp(self):
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.category = Category.objects.create(name="Salgados DEMO", active=True)
        self.client.force_login(self.gerente)

    def test_create_product(self):
        response = self.client.post(
            reverse("catalog:product_create"),
            {
                "name": "Pastel DEMO de queijo",
                "sku": "DEMO-QUEIJO",
                "category": self.category.pk,
                "sale_price": "12.50",
                "minimum_quantity": 4,
                "active": "on",
            },
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        product = Product.objects.get(sku="DEMO-QUEIJO")
        self.assertEqual(product.sale_price, Decimal("12.50"))
        self.assertEqual(product.stock.quantity, 0)
        self.assertEqual(product.stock.minimum_quantity, 4)

    def test_create_product_price_pt_br(self):
        response = self.client.post(
            reverse("catalog:product_create"),
            {
                "name": "Pastel DEMO de carne",
                "sku": "DEMO-CARNE",
                "category": self.category.pk,
                "sale_price": "1.234,56",
                "minimum_quantity": 2,
                "active": "on",
            },
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        product = Product.objects.get(sku="DEMO-CARNE")
        self.assertEqual(product.sale_price, Decimal("1234.56"))
