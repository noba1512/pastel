from django import forms

from apps.core.forms import style_form_widgets
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
        initial="0,00",
        help_text="Dinheiro na gaveta na abertura.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)
        self.fields["opening_amount"].widget.attrs["inputmode"] = "decimal"

    def clean_opening_amount(self):
        return parse_money_input(self.cleaned_data["opening_amount"])


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
            self.fields[name].widget.attrs["inputmode"] = "decimal"
            self.fields[name].widget.attrs["placeholder"] = "0,00"
            self.fields[name].widget.attrs["autocomplete"] = "off"
            self.fields[name].widget.attrs["class"] = (
                self.fields[name].widget.attrs.get("class", "") + " field-money"
            ).strip()
