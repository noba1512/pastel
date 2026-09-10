from django.views.generic import TemplateView

from apps.core.mixins import DashboardRequiredMixin
from apps.dashboard.services import dashboard_metrics


class DashboardView(DashboardRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(dashboard_metrics())
        return context
