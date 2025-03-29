from django.contrib import admin
from recipes.models import Ingredient, ShoppingCart, Favorite


class RecipeDurationFilter(admin.SimpleListFilter):
    title = "Время приготовления"
    parameter_name = "duration_category"

    def lookups(self, request, model_admin):
        return (
            ("fast", "Быстрое (≤10 мин)"),
            ("medium", "Среднее (11-30 мин)"),
            ("long", "Долгое (>30 мин)"),
        )

    def queryset(self, request, queryset):
        category = self.value()
        if category == "fast":
            return queryset.filter(cooking_time__lte=10)
        elif category == "medium":
            return queryset.filter(cooking_time__gt=10, cooking_time__lte=30)
        elif category == "long":
            return queryset.filter(cooking_time__gt=30)
        return queryset


@admin.register(Ingredient)
class IngredientAdminPanel(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit", "recipe_usage")
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit",)
    ordering = ("name",)

    @admin.display(description="Используется в рецептах")
    def recipe_usage(self, obj):
        return obj.recipeingredient_set.count()


@admin.register(ShoppingCart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")


@admin.register(Favorite)
class FavAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")
