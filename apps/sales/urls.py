from django.urls import path

from apps.sales import cash_views, views

app_name = "sales"

urlpatterns = [
    path("pdv/", views.PdvView.as_view(), name="pdv"),
    path("pdv/buscar/", views.PdvSearchView.as_view(), name="pdv_search"),
    path("pdv/finalizar/", views.PdvCheckoutView.as_view(), name="pdv_checkout"),
    path("caixa/", cash_views.CashListView.as_view(), name="cash_list"),
    path("caixa/abrir/", cash_views.CashOpenView.as_view(), name="cash_open"),
    path("caixa/fechar/", cash_views.CashCloseView.as_view(), name="cash_close"),
    path("caixa/<int:pk>/", cash_views.CashDetailView.as_view(), name="cash_detail"),
    path("caixa/<int:pk>/fechar/", cash_views.CashCloseView.as_view(), name="cash_close_pk"),
    path("caixa/<int:pk>/imprimir/", cash_views.CashPrintView.as_view(), name="cash_print"),
    path("vendas/", views.SaleListView.as_view(), name="list"),
    path("vendas/<int:pk>/", views.SaleDetailView.as_view(), name="detail"),
    path("vendas/<int:pk>/comprovante/", views.SaleReceiptView.as_view(), name="receipt"),
    path("vendas/<int:pk>/imprimir/", views.SalePrintView.as_view(), name="print"),
    path("vendas/<int:pk>/cancelar/", views.SaleCancelView.as_view(), name="cancel"),
]
