from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Кастомизированная модель пользователя"""

    email = models.EmailField("Электронная почта", unique=True, max_length=254)
    first_name = models.CharField("Имя", max_length=60)
    last_name = models.CharField("Фамилия", max_length=60)
    username = models.CharField(
        "Псевдоним",
        max_length=60,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9@.+\-_]+$",
                message="Псевдоним может содержать только буквы, цифры и символы @/./+/-/_",
                code="invalid_username_custom",
            )
        ],
    )
    avatar = models.ImageField(
        "Аватар",
        upload_to="avatars/users/",
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

    def __str__(self):
        return f"{self.email}"


class Subscription(models.Model):
    """Модель подписки на юзеров"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="followers",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="authors",
    )
