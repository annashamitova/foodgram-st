from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Recipe(models.Model):
    """Модель рецепта блюда"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe_list",
        verbose_name="Автор рецепта",
    )
    title = models.CharField(max_length=256, verbose_name="Название рецепта")
    description = models.TextField(verbose_name="Описание рецепта")
    cook_time = models.PositiveIntegerField(
        verbose_name="Время приготовления (мин)",
        validators=[MinValueValidator(1, message="Минимальное время — 1 минута")],
    )
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Изображение")
    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )

    class Meta:
        ordering = ("-cook_time",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецепта с ингредиентом"""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredients_detail"
    )
    ingredient = models.ForeignKey(
        "Ingredient", on_delete=models.CASCADE, related_name="recipes_detail"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1, message="Минимальное количество — 1")],
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient_relation",
            )
        ]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128, unique=True, verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=64, verbose_name="Единица измерения"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_carts"
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_user_recipe_in_cart",
            )
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.user} -> {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_recipes"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by"
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite_recipe",
            )
        ]
        ordering = ["user"]

    def __str__(self):
        return f"Избранное: {self.user} – {self.recipe}"
