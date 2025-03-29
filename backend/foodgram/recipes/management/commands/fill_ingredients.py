import os
import json
from django.core.management.base import BaseCommand

from foodgram.recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            base_dir = os.path.abspath(os.getcwd())
            fixture_path = os.path.join(base_dir, "recipes", "management", "data", "ingredients.json")

            with open(fixture_path, encoding="utf-8") as file:
                data = json.load(file)

            ingredients_to_create = [Ingredient(**item) for item in data]

            Ingredient.objects.bulk_create(ingredients_to_create, ignore_conflicts=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Добавлено {len(ingredients_to_create)} новых ингредиентов."
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при импорте {fixture_path}: {e}")
            )
