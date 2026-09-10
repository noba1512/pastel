from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product
from apps.core.permissions import GROUP_ADMIN, GROUP_CASHIER, GROUP_MANAGER, ensure_groups
from apps.inventory.models import Stock
from apps.inventory.services import register_entry


DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = "Cria dados DEMO fictícios. Não representa o cardápio real da Pastel da TATI."

    @transaction.atomic
    def handle(self, *args, **options):
        ensure_groups()
        groups = {group.name: group for group in Group.objects.filter(name__in=[
            GROUP_ADMIN, GROUP_MANAGER, GROUP_CASHIER
        ])}

        users = [
            ("admin.demo", GROUP_ADMIN, "Ana", "Demo"),
            ("gerente.demo", GROUP_MANAGER, "Gil", "Demo"),
            ("caixa.demo", GROUP_CASHIER, "Caio", "Demo"),
        ]
        for username, group_name, first, last in users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "is_active": True},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            user.groups.set([groups[group_name]])

        categories = {
            "Salgados DEMO": None,
            "Bebidas DEMO": None,
            "Doces DEMO": None,
        }
        for name in categories:
            category, _ = Category.objects.get_or_create(name=name, defaults={"active": True})
            categories[name] = category

        products = [
            ("Pastel DEMO de queijo", "DEMO-QUEIJO", "Salgados DEMO", Decimal("12.50"), 5, 20),
            ("Pastel DEMO de carne", "DEMO-CARNE", "Salgados DEMO", Decimal("13.00"), 5, 18),
            ("Pastel DEMO de palmito", "DEMO-PALMITO", "Salgados DEMO", Decimal("14.00"), 3, 10),
            ("Refrigerante DEMO lata", "DEMO-REFRI", "Bebidas DEMO", Decimal("7.00"), 6, 24),
            ("Suco DEMO natural", "DEMO-SUCO", "Bebidas DEMO", Decimal("8.50"), 4, 12),
            ("Pudim DEMO fatia", "DEMO-PUDIM", "Doces DEMO", Decimal("9.00"), 3, 8),
        ]
        for name, sku, category_name, price, minimum, qty in products:
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": categories[category_name],
                    "sale_price": price,
                    "active": True,
                },
            )
            stock, stock_created = Stock.objects.get_or_create(
                product=product,
                defaults={"quantity": 0, "minimum_quantity": minimum},
            )
            if stock_created or stock.quantity == 0:
                admin_user = User.objects.get(username="admin.demo")
                register_entry(
                    product=product,
                    quantity=qty,
                    user=admin_user,
                    reason="Carga inicial DEMO",
                )
            stock.minimum_quantity = minimum
            stock.save(update_fields=["minimum_quantity", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                "Dados DEMO criados. Logins: admin.demo / gerente.demo / caixa.demo "
                f"(senha {DEMO_PASSWORD}). Produtos são fictícios."
            )
        )
