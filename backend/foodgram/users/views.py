from django_filters import FilterSet, NumberFilter
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Recipe
from users.models import User
from users.serializers import Pagination, ProfileUserSerializer, AvatarSerializer


class UserViewSet(DjoserUserViewSet):
    """
    Наследуемся от стандартного djoser.views.UserViewSet,
    чтобы переопределить/добавить нужные методы.
    """

    pagination_class = Pagination
    queryset = User.objects.all()
    serializer_class = ProfileUserSerializer

    def get_permissions(self):
        """Переопределяем разрешения для разных эндпоинтов."""
        if self.action in ["me", "avatar"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request, *args, **kwargs):
        """
        Метод для обновления (PUT) или удаления (DELETE) аватара
        текущего пользователя по эндпоинту /users/me/avatar/.
        """
        user = request.user

        if request.method == "PUT":
            serializer = AvatarSerializer(
                user, data=request.data, partial=True, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"avatar": user.avatar.url}, status=200)

        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response({"detail": "Аватар успешно удалён."}, status=204)
        return Response({"detail": "Аватар отсутствует."}, status=400)


class RecipePagination(PageNumberPagination):
    """Пагинация рецептов"""

    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class RecipeFilter(FilterSet):
    """
    Фильтр для поиска рецептов
    """

    author = NumberFilter(field_name="author_id")
    is_in_shopping_cart = NumberFilter(method="filter_in_shopping_cart")
    is_favorited = NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ["author", "is_in_shopping_cart", "is_favorited"]

    def filter_in_shopping_cart(self, recipes_qs, name, value):
        """
        рецепты, находящиеся в корзине текущего пользователя
        """
        user = self.request.user
        if not user.is_authenticated:
            return recipes_qs.none() if value == 1 else recipes_qs

        if value == 1:
            return recipes_qs.filter(in_shopping_carts__user=user)
        return recipes_qs

    def filter_is_favorited(self, recipes_qs, name, value):
        """
        рецепты, находящиеся в избранном пользователя
        """
        user = self.request.user
        if not user.is_authenticated:
            return recipes_qs.none() if value == 1 else recipes_qs

        if value == 1:
            return recipes_qs.filter(in_favorites__user=user)
        return recipes_qs