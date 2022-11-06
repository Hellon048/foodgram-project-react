import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from food_gram.settings import BASE_DIR
from recipes.models import Ingredient

PROJECT_DIR = Path(BASE_DIR).resolve().joinpath('data')
FILE_TO_OPEN = PROJECT_DIR / "ingredients.csv"


class Command(BaseCommand):
    help = 'Заливка csv файлов'

    def handle(self, *args, **options):
        # Парсинг ингридиентов
        with open(FILE_TO_OPEN, encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                status, created = Ingredient.objects.update_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )

        print('Все ингридиенты загружены.')
