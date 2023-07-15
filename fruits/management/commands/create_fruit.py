import datetime

from django.core.management import BaseCommand
from fruits.models import *


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('PRODUCT CREATING')
        if not Fruit.objects.all().exists():
            Fruit.objects.bulk_create([
                Fruit.objects.create(name='Яблука', total_count=75, price=4, count=5, type_operation=TypeOperationChoices.choices[0][0], date_operation=datetime.datetime.now()),
                Fruit.objects.create(name='Ананаси', total_count=75, price=4, count=5, type_operation=TypeOperationChoices.choices[0][0], date_operation=datetime.datetime.now()),
                Fruit.objects.create(name='Банани', total_count=75, price=4, count=5, type_operation=TypeOperationChoices.choices[0][0], date_operation=datetime.datetime.now()),
                Fruit.objects.create(name='Персики', total_count=75, price=4, count=5, type_operation=TypeOperationChoices.choices[0][0], date_operation=datetime.datetime.now()),
            ])