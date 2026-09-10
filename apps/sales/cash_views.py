from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.exceptions import DomainError
from apps.core.mixins import SellRequiredMixin
from apps.core.permissions import can_view_all_cash_sessions, can_view_cash_session
from apps.sales.cash import (
    can_close_session,
    close_cash_session,
    get_open_session,
    open_cash_session,
    session_totals,
)
from apps.sales.forms import CashCloseForm, CashOpenForm
from apps.sales.models import CashSession
from apps.sales.receipt_print import print_cash_close_receipt, print_cash_open_receipt


class CashListView(SellRequiredMixin, ListView):
    model = CashSession
    template_name = "sales/cash_list.html"
    context_object_name = "sessions"
    paginate_by = 25

    def get_queryset(self):
        queryset = CashSession.objects.select_related("operator", "closed_by")
        if not can_view_all_cash_sessions(self.request.user):
            queryset = queryset.filter(operator=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_session"] = get_open_session(self.request.user)
        return context


class CashOpenView(SellRequiredMixin, View):
    template_name = "sales/cash_open.html"

    def get(self, request):
        existing = get_open_session(request.user)
        if existing:
            messages.info(request, f"Caixa {existing.number} já está aberto.")
            return redirect("sales:pdv")
        return render(request, self.template_name, {"form": CashOpenForm()})

    def post(self, request):
        existing = get_open_session(request.user)
        if existing:
            messages.info(request, f"Caixa {existing.number} já está aberto.")
            return redirect("sales:pdv")
        form = CashOpenForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        try:
            session = open_cash_session(
                operator=request.user,
                opening_amount=form.cleaned_data["opening_amount"],
            )
        except DomainError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})
        print_cash_open_receipt(session)
        messages.success(request, f"Caixa {session.number} aberto. Comprovante enviado.")
        return redirect("sales:pdv")


class CashCloseView(SellRequiredMixin, View):
    template_name = "sales/cash_close.html"

    def _session(self, request, pk):
        if pk:
            session = get_object_or_404(
                CashSession.objects.select_related("operator"), pk=pk
            )
        else:
            session = get_open_session(request.user)
            if session is None:
                return None
        if not can_view_cash_session(request.user, session):
            raise PermissionDenied("Você não pode ver este caixa.")
        return session

    def get(self, request, pk=None):
        session = self._session(request, pk)
        if session is None:
            messages.error(request, "Nenhum caixa aberto. Abra o caixa para vender.")
            return redirect("sales:cash_open")
        if session.status != CashSession.Status.OPEN:
            messages.info(request, f"Caixa {session.number} já está fechado.")
            return redirect("sales:cash_detail", pk=session.pk)
        if not can_close_session(request.user, session):
            raise PermissionDenied("Você não pode fechar este caixa.")
        totals = session_totals(session)
        return render(
            request,
            self.template_name,
            {
                "form": CashCloseForm(),
                "session": session,
                "totals": totals,
            },
        )

    def post(self, request, pk=None):
        session = self._session(request, pk)
        if session is None:
            messages.error(request, "Nenhum caixa aberto.")
            return redirect("sales:cash_open")
        if not can_close_session(request.user, session):
            raise PermissionDenied("Você não pode fechar este caixa.")
        form = CashCloseForm(request.POST)
        totals = session_totals(session)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "session": session, "totals": totals},
            )
        try:
            session = close_cash_session(
                session=session,
                user=request.user,
                counted_cash=form.cleaned_data["counted_cash"],
                counted_pix=form.cleaned_data.get("counted_pix") or "",
                counted_debit=form.cleaned_data.get("counted_debit") or "",
                counted_credit=form.cleaned_data.get("counted_credit") or "",
                notes=form.cleaned_data.get("notes") or "",
            )
        except DomainError as exc:
            messages.error(request, str(exc))
            return render(
                request,
                self.template_name,
                {"form": form, "session": session, "totals": totals},
            )
        print_cash_close_receipt(session)
        messages.success(request, f"Caixa {session.number} fechado. Comprovante enviado.")
        return redirect("sales:cash_detail", pk=session.pk)


class CashDetailView(SellRequiredMixin, DetailView):
    model = CashSession
    template_name = "sales/cash_detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return CashSession.objects.select_related("operator", "closed_by")

    def get_object(self, queryset=None):
        session = super().get_object(queryset)
        if not can_view_cash_session(self.request.user, session):
            raise PermissionDenied("Você não pode ver este caixa.")
        return session

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_close"] = can_close_session(self.request.user, self.object)
        if self.object.status == CashSession.Status.OPEN:
            context["totals"] = session_totals(self.object)
        return context


class CashPrintView(SellRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(
            CashSession.objects.select_related("operator", "closed_by"), pk=pk
        )
        if not can_view_cash_session(request.user, session):
            raise PermissionDenied("Você não pode imprimir este caixa.")
        kind = request.POST.get("tipo", "fechamento")
        if kind == "abertura":
            result = print_cash_open_receipt(session)
        else:
            if session.status != CashSession.Status.CLOSED:
                messages.error(request, "Feche o caixa para imprimir a conferência.")
                return redirect("sales:cash_detail", pk=session.pk)
            result = print_cash_close_receipt(session)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": result.ok,
                    "printed": result.ok,
                    "print_method": result.method,
                    "print_error": result.error,
                }
            )
        messages.success(request, f"Comprovante de {session.number} enviado.")
        return redirect("sales:cash_detail", pk=session.pk)
