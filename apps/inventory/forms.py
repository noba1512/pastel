from django import forms

from apps.catalog.models import Product
from apps.core.forms import style_form_widgets


class StockEntryForm(forms.Form):
    product = forms.ModelChoiceField(
        label="Produto",
        queryset=Product.objects.filter(active=True).order_by("name"),
    )
    quantity = forms.IntegerField(label="Quantidade", min_value=1)
    reason = forms.CharField(label="Observação / motivo", max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)


class StockAdjustForm(forms.Form):
    DIRECTION_CHOICES = (
        ("in", "Aumentar estoque"),
        ("out", "Reduzir estoque"),
    )
    product = forms.ModelChoiceField(
        label="Produto",
        queryset=Product.objects.all().order_by("name"),
    )
    direction = forms.ChoiceField(label="Tipo de ajuste", choices=DIRECTION_CHOICES)
    quantity = forms.IntegerField(label="Quantidade", min_value=1)
    reason = forms.CharField(label="Motivo", max_length=200)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)
