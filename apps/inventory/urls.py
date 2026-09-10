from django.urls import path

from apps.inventory import views

app_name = "inventory"

urlpatterns = [
    path("estoque/", views.StockListView.as_view(), name="stock_list"),
    path("estoque/entrada/", views.StockEntryView.as_view(), name="stock_entry"),
    path("estoque/ajuste/", views.StockAdjustView.as_view(), name="stock_adjust"),
    path("estoque/movimentacoes/", views.StockMovementListView.as_view(), name="movement_list"),
]
