from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.core.permissions import ALL_GROUPS, GROUP_ADMIN, GROUP_CASHIER, GROUP_MANAGER


class Command(BaseCommand):
    help = "Cria grupos e permissões iniciais. Idempotente."

    def handle(self, *args, **options):
        groups = {name: Group.objects.get_or_create(name=name)[0] for name in ALL_GROUPS}

        catalog_perms = Permission.objects.filter(
            content_type__app_label="catalog",
            codename__in=[
                "view_category",
                "add_category",
                "change_category",
                "view_product",
                "add_product",
                "change_product",
            ],
        )
        inventory_perms = Permission.objects.filter(
            content_type__app_label="inventory",
            codename__in=[
                "view_stock",
                "change_stock",
                "view_stockmovement",
                "add_stockmovement",
            ],
        )
        sales_perms = Permission.objects.filter(
            content_type__app_label="sales",
            codename__in=[
                "view_sale",
                "add_sale",
                "change_sale",
                "view_saleitem",
                "view_payment",
                "view_cashsession",
                "add_cashsession",
                "change_cashsession",
            ],
        )
        user_perms = Permission.objects.filter(
            content_type__app_label="auth",
            codename__in=["view_user", "add_user", "change_user"],
        )

        groups[GROUP_ADMIN].permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=["catalog", "inventory", "sales", "auth", "admin"]
            )
        )
        groups[GROUP_MANAGER].permissions.set(
            list(catalog_perms) + list(inventory_perms) + list(sales_perms) + list(
                Permission.objects.filter(content_type__app_label="auth", codename="view_user")
            )
        )
        groups[GROUP_CASHIER].permissions.set(
            list(
                Permission.objects.filter(
                    content_type__app_label__in=["catalog", "sales"],
                    codename__in=[
                        "view_product",
                        "view_category",
                        "view_sale",
                        "add_sale",
                        "view_payment",
                        "view_cashsession",
                        "add_cashsession",
                        "change_cashsession",
                    ],
                )
            )
        )

        ContentType.objects.get_for_model(Permission)
        self.stdout.write(self.style.SUCCESS("Grupos e permissões prontos."))
