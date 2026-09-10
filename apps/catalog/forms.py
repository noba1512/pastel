from django import forms

from apps.catalog.models import Category, Product
from apps.core.exceptions import DomainError
from apps.core.forms import mark_money_field, style_form_widgets
from apps.inventory.models import Stock
from apps.sales.services import format_money_br, parse_money_input


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "active"]
        labels = {"name": "Nome", "active": "Ativa"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form_widgets(self)


class ProductForm(forms.ModelForm):
    minimum_quantity = forms.IntegerField(
        label="Estoque mínimo",
        min_value=0,
        initial=0,
    )
    sale_price = forms.CharField(label="Preço")

    class Meta:
        model = Product
        fields = ["name", "sku", "category", "active"]
        labels = {
            "name": "Nome",
            "sku": "SKU",
            "category": "Categoria",
            "active": "Ativo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(active=True)
        self.order_fields(
            ["name", "sku", "category", "sale_price", "minimum_quantity", "active"]
        )
        style_form_widgets(self)
        mark_money_field(self.fields["sale_price"])
        if self.instance.pk and self.instance.sale_price is not None:
            self.initial["sale_price"] = format_money_br(self.instance.sale_price)
        if self.instance.pk:
            if self.instance.category_id:
                self.fields["category"].queryset = Category.objects.filter(
                    active=True
                ) | Category.objects.filter(pk=self.instance.category_id)
            stock = getattr(self.instance, "stock", None)
            if stock:
                self.fields["minimum_quantity"].initial = stock.minimum_quantity

    def clean_sale_price(self):
        try:
            price = parse_money_input(self.cleaned_data["sale_price"])
        except DomainError as exc:
            raise forms.ValidationError(str(exc)) from exc
        if price < 0:
            raise forms.ValidationError("O preço deve ser maior ou igual a zero.")
        return price

    def save(self, commit=True):
        product = super().save(commit=False)
        product.sale_price = self.cleaned_data["sale_price"]
        if commit:
            product.save()
            stock, _created = Stock.objects.get_or_create(
                product=product,
                defaults={"quantity": 0, "minimum_quantity": 0},
            )
            stock.minimum_quantity = self.cleaned_data["minimum_quantity"]
            stock.save(update_fields=["minimum_quantity", "updated_at"])
        return product
