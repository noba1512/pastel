from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Pastel da TATI"
admin.site.site_title = "Pastel da TATI"
admin.site.index_title = "Manutenção técnica"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.sales.urls")),
]
