from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from users.models import User, Subscription


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Административная панель для кастомного пользователя.
    """

    list_display = (
        "id",
        "username",
        "email",
        "full_name",
        "avatar_preview",
        "recipe_count",
        "followers_count",
        "following_count",
    )
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("id",)
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональные данные",
            {"fields": ("username", "first_name", "last_name", "avatar")},
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    @admin.display(description="ФИО")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    @admin.display(description="Аватар")
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.avatar.url,
            )
        return "Нет аватара"

    @admin.display(description="Рецептов")
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description="Подписчиков")
    def followers_count(self, obj):
        return obj.followers.count()

    @admin.display(description="Подписок")
    def following_count(self, obj):
        return obj.following.count()


@admin.register(Subscription)
class CustomSubscriptionAdmin(admin.ModelAdmin):
    """
    Административная панель для управления подписками.
    """

    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user", "author")
