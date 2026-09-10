from django import forms

from apps.core.exceptions import DomainError
from apps.core.forms import mark_money_field, style_form_widgets
from apps.sales.models import Payment, Sale
from apps.sales.services import parse_money_input


class SaleFilterForm(forms.Form):
    date_from = forms.DateField(label="De", required=False, input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    date_to = forms.DateField(label="Até", required=False, input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    operator = forms.IntegerField(label="Operador", required=False)
    method = forms.ChoiceField(
        label="Pagamento",
        required=False,
        choices=[("", "Todas")] + list(Payment.Method.choices),
        widget=forms.Select(),
    )
    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[("", "Todos")] + list(Sale.Status.choices),
        widget=forms.Select(),
    )


class SaleCancelForm(forms.Form):
    reason = forms.CharField(
        label="Motivo do cancelamento",
        max_length=240,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)


class CashOpenForm(forms.Form):
    opening_amount = forms.CharField(
        label="Fundo de caixa",
        required=False,
        help_text="Dinheiro na gaveta na abertura.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)
        mark_money_field(self.fields["opening_amount"])

    def clean_opening_amount(self):
        raw = (self.cleaned_data.get("opening_amount") or "").strip()
        if not raw:
            return parse_money_input("0")
        try:
            return parse_money_input(raw)
        except DomainError as exc:
            raise forms.ValidationError(str(exc)) from exc


class CashCloseForm(forms.Form):
    counted_cash = forms.CharField(
        label="Dinheiro conferido",
        help_text="Fundo + vendas em dinheiro.",
    )
    counted_pix = forms.CharField(
        label="PIX conferido",
        required=False,
    )
    counted_debit = forms.CharField(
        label="Débito conferido",
        required=False,
    )
    counted_credit = forms.CharField(
        label="Crédito conferido",
        required=False,
    )
    notes = forms.CharField(
        label="Observação",
        required=False,
        max_length=240,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Obrigatório se o dinheiro divergir.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)
        for name in ("counted_cash", "counted_pix", "counted_debit", "counted_credit"):
            mark_money_field(self.fields[name])
