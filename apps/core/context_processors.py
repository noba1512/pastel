from apps.core import permissions as perm
from apps.sales.cash import get_open_session

MOBILE_PRIMARY = (
    "sales:pdv",
    "sales:cash_list",
    "sales:list",
    "dashboard:index",
    "inventory:stock_list",
)

NAV_FAMILY = {
    "sales:cash_open": "sales:cash_list",
    "sales:cash_close": "sales:cash_list",
    "sales:cash_close_pk": "sales:cash_list",
    "sales:cash_detail": "sales:cash_list",
    "sales:cash_print": "sales:cash_list",
    "sales:detail": "sales:list",
    "sales:receipt": "sales:list",
    "catalog:product_create": "catalog:product_list",
    "catalog:product_update": "catalog:product_list",
    "catalog:category_create": "catalog:category_list",
    "catalog:category_update": "catalog:category_list",
    "inventory:stock_entry": "inventory:stock_list",
    "inventory:stock_adjust": "inventory:stock_list",
    "inventory:movement_list": "inventory:stock_list",
    "accounts:user_create": "accounts:user_list",
    "accounts:user_update": "accounts:user_list",
}


def navigation(request):
    user = request.user
    items = []
    if user.is_authenticated:
        if perm.can_access_dashboard(user):
            items.append({"name": "Dashboard", "url_name": "dashboard:index"})
        if perm.can_sell(user):
            items.append({"name": "PDV", "url_name": "sales:pdv"})
            items.append({"name": "Caixa", "url_name": "sales:cash_list"})
            items.append({"name": "Vendas", "url_name": "sales:list"})
        if perm.can_manage_catalog(user):
            items.append({"name": "Produtos", "url_name": "catalog:product_list"})
            items.append({"name": "Categorias", "url_name": "catalog:category_list"})
        if perm.can_view_stock(user):
            items.append({"name": "Estoque", "url_name": "inventory:stock_list"})
        if perm.can_view_users(user):
            items.append({"name": "Usuários", "url_name": "accounts:user_list"})

    by_name = {item["url_name"]: item for item in items}
    mobile_nav = [by_name[name] for name in MOBILE_PRIMARY if name in by_name][:4]
    mobile_more = [item for item in items if item not in mobile_nav]
    current = getattr(request.resolver_match, "view_name", "") or ""
    current_nav = NAV_FAMILY.get(current, current)
    open_session = (
        get_open_session(user) if user.is_authenticated and perm.can_sell(user) else None
    )

    return {
        "nav_items": items,
        "mobile_nav": mobile_nav,
        "mobile_more": mobile_more,
        "current_view": current,
        "current_nav": current_nav,
        "is_pdv": current == "sales:pdv",
        "user_role_name": perm.primary_group_name(user) if user.is_authenticated else "",
        "can_apply_discount": perm.can_apply_discount(user) if user.is_authenticated else False,
        "can_manage_users": perm.can_manage_users(user) if user.is_authenticated else False,
        "can_adjust_stock": perm.can_adjust_stock(user) if user.is_authenticated else False,
        "can_cancel_sale": perm.can_cancel_sale(user) if user.is_authenticated else False,
        "open_cash_session": open_session,
        "can_sell": perm.can_sell(user) if user.is_authenticated else False,
    }
