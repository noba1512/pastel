from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("produtos/", views.ProductListView.as_view(), name="product_list"),
    path("produtos/novo/", views.ProductCreateView.as_view(), name="product_create"),
    path("produtos/<int:pk>/editar/", views.ProductUpdateView.as_view(), name="product_update"),
    path(
        "produtos/<int:pk>/alternar/",
        views.ProductDeactivateView.as_view(),
        name="product_toggle",
    ),
    path("categorias/", views.CategoryListView.as_view(), name="category_list"),
    path("categorias/nova/", views.CategoryCreateView.as_view(), name="category_create"),
    path(
        "categorias/<int:pk>/editar/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
]
