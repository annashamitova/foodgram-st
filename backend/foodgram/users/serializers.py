import base64
from django.core.files.base import ContentFile  # Для работы с файлами из строк (base64)
from django.shortcuts import get_object_or_404  # Для получения объекта или возврата 404
from djoser.serializers import UserSerializer, User  # Базовые сериализаторы Djoser
from rest_framework import serializers, status  # Основные инструменты DRF
from rest_framework.decorators import action  # Декоратор для добавления кастомных эндпоинтов
from rest_framework.pagination import LimitOffsetPagination  # Пагинация по offset/limit
from rest_framework.permissions import IsAuthenticated  # Право доступа только авторизованным
from rest_framework.response import Response  # Ответы от view

# Импорты из проекта
from recipes.models import Recipe  # Модель рецепта
from users.models import Subscription  # Модель подписки на пользователя
from users.utils import Base64ImageField  # Кастомное поле для обработки base64 изображений


class Pagination(LimitOffsetPagination):
    """
    Пагинация для API.
    Устанавливает максимальное количество элементов на странице — 100.
    """

    default_limit = 10  # Стандартное количество записей на странице
    max_limit = 100     # Максимальное количество записей, которое можно запросить за один раз


class ProfileUserSerializer(UserSerializer):
    """
    Сериализатор профиля пользователя.
    Добавляет поля: is_subscribed (подписан ли текущий пользователь) и avatar (аватар).
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ("is_subscribed", "avatar")

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.followers.filter(user=request.user).exists()

    def get_avatar(self, obj):
        """Возвращает URL аватара, если он существует."""
        return obj.avatar.url if obj.avatar else None


class AvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для загрузки аватара пользователя через строку base64.
    Преобразует данные из base64 в файл Django и сохраняет его.
    """

    avatar = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["avatar"]

    def validate_avatar(self, avatar_data):
        """
        Валидация и декодирование строки base64.
        Возвращает объект ContentFile, готовый к записи в модель.
        """
        if "avatar" not in self.initial_data:
            raise serializers.ValidationError(
                "Поле 'avatar' обязательно для передачи."
            )

        if not avatar_data:
            raise serializers.ValidationError("Поле 'avatar' не может быть пустым.")

        try:
            image_format, image_str = avatar_data.split(";base64,")
            extension = image_format.split("/")[-1]
            decoded_image = base64.b64decode(image_str)
        except Exception:
            raise serializers.ValidationError("Ошибка при обработке изображения.")

        return ContentFile(decoded_image, name=f"user_avatar.{extension}")

    def update(self, instance, validated_data):
        """
        Обновляет аватар пользователя.
        Если файл не предоставлен — выбрасывает ошибку.
        """
        avatar_file = validated_data.get("avatar")
        if not avatar_file:
            raise serializers.ValidationError(
                {"avatar": "Файл аватара должен быть указан."}
            )
        instance.avatar = avatar_file
        instance.save()
        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Краткий сериализатор для рецептов.
    Используется в подписках, чтобы показать список рецептов без лишних данных.
    """

    image = Base64ImageField()  # Поле для изображения в формате base64

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSubscriptionSerializer(ProfileUserSerializer):
    """
    Сериализатор для отображения информации о подписке на пользователя.
    Включает краткий список рецептов и их общее количество.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta:
        model = User
        fields = ProfileUserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        """
        Возвращает ограниченное количество рецептов пользователя.
        Ограничение задается параметром `recipes_limit` в query-параметрах.
        """
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")

        queryset = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[: int(recipes_limit)]

        return RecipeShortSerializer(queryset, many=True, context={"request": request}).data

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """
        Кастомный эндпоинт для подписки или отписки от пользователя.
        POST — подписка, DELETE — отписка.
        """
        user = request.user
        author = self.get_object()

        if request.method == "POST":
            if user == author:
                return Response(
                    {"error": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )

            if not created:
                return Response(
                    {"error": f"Вы уже подписаны на пользователя {author.username}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = UserSubscriptionSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE-запрос: удаление подписки
        get_object_or_404(Subscription, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)