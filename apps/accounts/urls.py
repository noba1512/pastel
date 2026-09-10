from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("", views.PostLoginView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("entrar/", views.PostLoginView.as_view(), name="post_login"),
    path("usuarios/", views.UserListView.as_view(), name="user_list"),
    path("usuarios/novo/", views.UserCreateView.as_view(), name="user_create"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="user_update"),
]
