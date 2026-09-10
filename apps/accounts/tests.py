from django.test import TestCase
from django.urls import reverse

from apps.core.permissions import GROUP_ADMIN, GROUP_CASHIER, GROUP_MANAGER
from apps.core.test_utils import make_product, make_user, open_test_session


class LoginTests(TestCase):
    def test_login_caixa_goes_to_pdv(self):
        make_user("caixa1", GROUP_CASHIER)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "caixa1", "password": "senha12345"},
        )
        self.assertRedirects(
            response, reverse("sales:pdv"), fetch_redirect_response=False
        )

    def test_login_gerente_goes_to_dashboard(self):
        make_user("gerente1", GROUP_MANAGER)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "gerente1", "password": "senha12345"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_login_admin_goes_to_dashboard(self):
        make_user("admin1", GROUP_ADMIN)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin1", "password": "senha12345"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_inactive_user_cannot_login(self):
        make_user("parado", GROUP_CASHIER, is_active=False)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "parado", "password": "senha12345"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "inativo")


class PermissionTests(TestCase):
    def setUp(self):
        self.caixa = make_user("caixa1", GROUP_CASHIER)
        self.gerente = make_user("gerente1", GROUP_MANAGER)
        self.admin = make_user("admin1", GROUP_ADMIN)

    def test_caixa_cannot_open_users_or_stock_or_catalog(self):
        self.client.force_login(self.caixa)
        for name in (
            "accounts:user_list",
            "accounts:user_create",
            "inventory:stock_list",
            "inventory:stock_entry",
            "catalog:product_list",
            "catalog:category_list",
            "dashboard:index",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 403, name)

    def test_caixa_can_open_pdv(self):
        open_test_session(self.caixa)
        self.client.force_login(self.caixa)
        response = self.client.get(reverse("sales:pdv"))
        self.assertEqual(response.status_code, 200)

    def test_gerente_can_open_dashboard_and_catalog(self):
        self.client.force_login(self.gerente)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("catalog:product_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory:stock_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:user_list")).status_code, 200)

    def test_gerente_cannot_create_user(self):
        self.client.force_login(self.gerente)
        response = self.client.get(reverse("accounts:user_create"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("accounts:user_create"),
            {
                "username": "novo.caixa",
                "first_name": "Novo",
                "password": "senha12345",
                "group": self.caixa.groups.first().pk,
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("accounts:user_list"))
        from django.contrib.auth.models import User

        created = User.objects.get(username="novo.caixa")
        self.assertTrue(created.check_password("senha12345"))
        self.assertTrue(created.groups.filter(name=GROUP_CASHIER).exists())
