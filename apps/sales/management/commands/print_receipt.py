from django.core.management.base import BaseCommand, CommandError

from apps.sales.models import Sale
from apps.sales.receipt_print import print_sale_receipt


class Command(BaseCommand):
    help = "Imprime comprovante térmico da venda (ESC/POS). Sem diálogo do navegador."

    def add_arguments(self, parser):
        parser.add_argument("number", help="Número da venda, ou 'last' para a última.")

    def handle(self, *args, **options):
        number = options["number"]
        if number == "last":
            sale = Sale.objects.order_by("-pk").first()
            if sale is None:
                raise CommandError("Nenhuma venda encontrada.")
        else:
            sale = Sale.objects.filter(number=number).first()
            if sale is None:
                raise CommandError(f"Venda {number} não encontrada.")
        result = print_sale_receipt(sale)
        self.stdout.write(f"Cupom {sale.number} via {result.method}.")
        if result.error:
            self.stdout.write(self.style.WARNING(result.error))
