from django.contrib.auth.models import Group

GROUP_ADMIN = "Administrador"
GROUP_MANAGER = "Gerente"
GROUP_CASHIER = "Caixa"

ALL_GROUPS = (GROUP_ADMIN, GROUP_MANAGER, GROUP_CASHIER)


def _in_group(user, name):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=name).exists()


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or _in_group(user, GROUP_ADMIN))


def is_manager(user):
    return is_admin(user) or _in_group(user, GROUP_MANAGER)


def is_cashier(user):
    return _in_group(user, GROUP_CASHIER) or is_manager(user)


def can_access_dashboard(user):
    return is_manager(user)


def can_sell(user):
    return user.is_authenticated and user.is_active and (
        is_admin(user) or is_manager(user) or _in_group(user, GROUP_CASHIER)
    )


def can_view_all_sales(user):
    return is_manager(user)


def can_view_sale(user, sale):
    if can_view_all_sales(user):
        return True
    return can_sell(user) and sale.operator_id == user.id


def can_cancel_sale(user):
    return is_manager(user)


def can_view_all_cash_sessions(user):
    return is_manager(user)


def can_view_cash_session(user, session):
    if can_view_all_cash_sessions(user):
        return True
    return can_sell(user) and session.operator_id == user.id


def can_apply_discount(user):
    return is_manager(user)


def can_manage_catalog(user):
    return is_manager(user)


def can_view_stock(user):
    return is_manager(user)


def can_adjust_stock(user):
    return is_manager(user)


def can_view_users(user):
    return is_manager(user)


def can_manage_users(user):
    return is_admin(user)


def primary_group_name(user):
    if not user.is_authenticated:
        return ""
    if user.is_superuser:
        return GROUP_ADMIN
    names = set(user.groups.values_list("name", flat=True))
    for name in ALL_GROUPS:
        if name in names:
            return name
    return ""


def default_home_url_name(user):
    if can_access_dashboard(user):
        return "dashboard:index"
    if can_sell(user):
        return "sales:pdv"
    return "accounts:login"


def ensure_groups():
    for name in ALL_GROUPS:
        Group.objects.get_or_create(name=name)
