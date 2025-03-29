from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipes.views import RecipeViewSet, IngredientViewSet, get_short_link

app_name = "recipes"

router = DefaultRouter()
router.register(r"recipes", RecipeViewSet, basename="recipes")
router.register(r"ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
    path("s/<int:recipe_id>/", get_short_link, name="short_link"),
]
