import base64
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, User
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Recipe
from users.models import Subscription
from users.utils import Base64ImageField


class Pagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class ProfileUserSerializer(UserSerializer):
    """Сериализатор профиля пользователя с дополнительными полями."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ("is_subscribed", "avatar")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.followers.filter(user=request.user).exists()

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["avatar"]

    def validate_avatar(self, avatar_data):
        """Декодирует строку base64 и создает объект файла."""
        if "avatar" not in self.initial_data:
            raise serializers.ValidationError(
                "Поле 'avatar' отсутствует в данных запроса."
            )

        if not avatar_data:
            raise serializers.ValidationError("Значение поля 'avatar' обязательно.")

        try:
            image_format, image_str = avatar_data.split(";base64,")
            extension = image_format.split("/")[-1]
            decoded_image = base64.b64decode(image_str)
        except Exception:
            raise serializers.ValidationError("Ошибка декодирования изображения.")

        return ContentFile(decoded_image, name=f"user_avatar.{extension}")

    def update(self, instance, validated_data):
        avatar_file = validated_data.get("avatar")
        if not avatar_file:
            raise serializers.ValidationError(
                {"avatar": "Обязательное поле 'avatar' не предоставлено."}
            )
        instance.avatar = avatar_file
        instance.save()
        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта"""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSubscriptionSerializer(ProfileUserSerializer):
    """Сериализатор подписок"""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta:
        model = User
        fields = ProfileUserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")

        queryset = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[: int(recipes_limit)]

        return RecipeShortSerializer(
            queryset, many=True, context={"request": request}
        ).data

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """Подписка и отписка на пользователя."""
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

            serializer = UserSubscriptionSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(Subscription, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
