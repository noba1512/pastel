from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from apps.accounts.forms import LoginForm, UserForm
from apps.core import permissions as perm
from apps.core.mixins import UsersManageRequiredMixin, UsersViewRequiredMixin


class LoginView(View):
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse(perm.default_home_url_name(request.user)))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        username = form.cleaned_data["username"]
        existing = User.objects.filter(username=username).first()
        if existing and not existing.is_active:
            messages.error(request, "Este usuário está inativo e não pode entrar.")
            return render(request, self.template_name, {"form": form})

        user = authenticate(
            request,
            username=username,
            password=form.cleaned_data["password"],
        )
        if user is None:
            messages.error(request, "Usuário ou senha inválidos.")
            return render(request, self.template_name, {"form": form})

        login(request, user)
        return redirect(reverse(perm.default_home_url_name(user)))


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("accounts:login")


class PostLoginView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        return redirect(reverse(perm.default_home_url_name(request.user)))


class UserListView(UsersViewRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 30

    def get_queryset(self):
        return User.objects.prefetch_related("groups").order_by("username")


class UserCreateView(UsersManageRequiredMixin, View):
    template_name = "accounts/user_form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": UserForm(is_create=True), "title": "Novo usuário"},
        )

    def post(self, request):
        form = UserForm(request.POST, is_create=True)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário criado.")
            return redirect("accounts:user_list")
        return render(request, self.template_name, {"form": form, "title": "Novo usuário"})


class UserUpdateView(UsersManageRequiredMixin, View):
    template_name = "accounts/user_form.html"

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": UserForm(instance=user, is_create=False),
                "title": f"Editar {user.username}",
                "editing": user,
            },
        )

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserForm(request.POST, instance=user, is_create=False)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário atualizado.")
            return redirect("accounts:user_list")
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Editar {user.username}", "editing": user},
        )
