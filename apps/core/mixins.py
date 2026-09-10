from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from apps.core import permissions as perm


class ActiveUserRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_active:
            raise PermissionDenied("Usuário inativo.")
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(ActiveUserRequiredMixin, UserPassesTestMixin):
    permission_check = None

    def test_func(self):
        if self.permission_check is None:
            return False
        return self.permission_check(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return super().handle_no_permission()


class DashboardRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_access_dashboard)


class SellRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_sell)


class CatalogRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_manage_catalog)


class StockViewRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_view_stock)


class StockAdjustRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_adjust_stock)


class UsersViewRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_view_users)


class UsersManageRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_manage_users)


class SalesHistoryRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_sell)


class CancelSaleRequiredMixin(RoleRequiredMixin):
    permission_check = staticmethod(perm.can_cancel_sale)
