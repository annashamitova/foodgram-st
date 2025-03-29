from django.db import transaction
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64


from recipes.models import (
    User,
    Recipe,
    RecipeIngredient,
    Ingredient,
    Favorite,
)
from users.serializers import ProfileUserSerializer
from users.utils import Base64ImageField


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта"""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["avatar"]

    def validate_avatar(self, base64_string):
        """Декодируем base64 и создаём файл-объект."""
        if "avatar" not in self.initial_data:
            raise serializers.ValidationError("Поле 'avatar' отсутствует в запросе.")

        if not base64_string:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")

        try:
            format, img_str = base64_string.split(";base64,")
            ext = format.split("/")[-1]
            decoded_img = base64.b64decode(img_str)
        except Exception:
            raise serializers.ValidationError("Некорректный формат изображения.")

        return ContentFile(decoded_img, name=f"user_avatar.{ext}")

    def update(self, instance, validated_data):
        if "avatar" not in validated_data:
            raise serializers.ValidationError({"avatar": "Поле 'avatar' обязательно."})
        instance.avatar = validated_data["avatar"]
        instance.save()
        return instance


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи одного ингредиента в рецепт.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        required=True,
        source="ingredient",
        error_messages={"does_not_exist": "Ингредиент с таким ID не найден."},
    )
    amount = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения связки "ингредиент в рецепте".
    """

    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeWriteSerializer(many=True, required=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "text", "cooking_time", "image", "ingredients")

    def validate_ingredients(self, ingredients_data):
        # проверка, что ингредиенты не пустые и не повторяются
        if not ingredients_data:
            raise serializers.ValidationError(
                "Рецепт должен содержать хотя бы один ингредиент."
            )
        ingredient_ids = [item["ingredient"].id for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты в рецепте не должны повторяться."
            )
        return ingredients_data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        if ingredients_data is None:
            raise serializers.ValidationError(
                {"ingredients": "Поле ingredients обязательно при обновлении."}
            )
        instance = super().update(instance, validated_data)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_recipe_ingredients(instance, ingredients_data)
        return instance

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item["ingredient"],
                amount=item["amount"],
            )
            for item in ingredients_data
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(ProfileUserSerializer):
    """
    Сериализатор для детального/листового чтения рецепта.
    """

    author = ProfileUserSerializer(read_only=True)

    # Список ингредиентов в виде массива {id, name, measurement_unit, amount}
    ingredients = IngredientInRecipeReadSerializer(
        many=True, read_only=True, source="recipe_ingredients"
    )

    # Флаги, вычисляемые на лету
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields

    def get_is_in_shopping_cart(self, obj):
        """
        Возвращаем True/False, есть ли этот рецепт в корзине у текущего пользователя.
        Используем «ленивую» форму: user.is_authenticated и ...
        """
        user = self.context["request"].user
        return (
            user.is_authenticated and obj.in_shopping_carts.filter(user=user).exists()
        )

    def get_is_favorited(self, obj):
        """
        Возвращаем True/False, есть ли этот рецепт в избранном у текущего пользователя.
        Аналогичная логика.
        """
        user = self.context["request"].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
