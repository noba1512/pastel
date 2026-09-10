from decimal import Decimal

from django.contrib.auth.models import Group, User

from apps.catalog.models import Category, Product
from apps.core.permissions import ensure_groups
from apps.inventory.models import Stock


def make_user(username, group_name, password="senha12345", **extra):
    ensure_groups()
    user = User.objects.create_user(
        username=username,
        password=password,
        is_active=extra.pop("is_active", True),
        **extra,
    )
    user.groups.add(Group.objects.get(name=group_name))
    return user


def make_product(name="Pastel DEMO teste", sku="DEMO-TEST", price="10.00", stock_qty=10, minimum=2):
    category, _ = Category.objects.get_or_create(name="Categoria DEMO", defaults={"active": True})
    product = Product.objects.create(
        name=name,
        sku=sku,
        category=category,
        sale_price=Decimal(price),
        active=True,
    )
    Stock.objects.create(product=product, quantity=stock_qty, minimum_quantity=minimum)
    return product


def open_test_session(user, amount="0.00"):
    from apps.sales.cash import open_cash_session

    return open_cash_session(operator=user, opening_amount=amount)
