from datetime import datetime

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters import FilterSet, CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (
    Recipe,
    Ingredient,
    ShoppingCart,
    Favorite,
    RecipeIngredient,
)
from users.permissions import IsAuthorOrReadOnly
from users.views import RecipeFilter, RecipePagination
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    IngredientSerializer,
)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Сохранение рецепта с автором."""
        serializer.save(author=self.request.user)

    def toggle_relation(self, request, pk, model, error_message, success_message):
        """
        Универсальный метод для добавления/удаления рецептов из Избранного и Корзины.
        """
        user = request.user
        recipe = Recipe.objects.filter(pk=pk).first()

        if recipe and request.method == "POST":
            obj, created = model.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response(
                    {"error": error_message.format(recipe.name)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeShortSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(model, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в корзину покупок."""
        return self.toggle_relation(
            request,
            pk,
            ShoppingCart,
            error_message='Рецепт "{}" уже в корзине.',
            success_message='Рецепт "{}" отсутствует в корзине.',
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self.toggle_relation(
            request,
            pk,
            Favorite,
            error_message='Рецепт "{}" уже в избранном.',
            success_message='Рецепт "{}" не найден в избранном.',
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Формирует и скачивает список покупок в формате .txt.
        """
        user = request.user
        cart_items = ShoppingCart.objects.filter(user=user).select_related("recipe")

        if not cart_items.exists():
            return Response({"error": "Ваша корзина пуста."}, status=400)

        recipe_ids = cart_items.values_list("recipe__id", flat=True)

        ingredients_qs = RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)

        ingredients_data = (
            ingredients_qs.values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        recipes = Recipe.objects.filter(id__in=recipe_ids)

        date_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        header = f"Список покупок (составлен: {date_str})\n"
        product_header = "№ | Продукт | Количество | Ед. изм.\n"
        recipe_header = "\nИспользуется в рецептах:\n"

        products = [
            f"{idx + 1} | {item['ingredient__name'].capitalize()} | {item['total_amount']} | {item['ingredient__measurement_unit']}"
            for idx, item in enumerate(ingredients_data)
        ]

        recipe_list = [
            f"- {recipe.name} (Автор: {recipe.author.first_name} {recipe.author.last_name or recipe.author.username})"
            for recipe in recipes
        ]

        content = "\n".join(
            [header, product_header, *products, recipe_header, *recipe_list]
        )

        return FileResponse(
            content,
            as_attachment=True,
            filename="shopping_list.txt",
            content_type="text/plain",
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.
        """
        return Response(
            {
                "short-link": request.build_absolute_uri(
                    reverse("recipes:short_link", kwargs={"recipe_id": pk})
                )
            },
            status=status.HTTP_200_OK,
        )


class IngredientFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ["name"]


class IngredientViewSet(ReadOnlyModelViewSet):
    """API для получения списка ингредиентов с фильтрацией"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


def get_short_link(request, recipe_id):
    """
    Обрабатывает короткую ссылку и перенаправляет на локальный URL рецепта.
    """
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f"/recipes/{recipe_id}/")
