from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    """
    Кастомная модель пользователя для проекта с продажей словарей.
    Добавлен баланс для учёта покупок и продаж.
    """
    balance = models.DecimalField(
        max_digits=10,  # до 9 999 999.99
        decimal_places=2,
        default=0.00,
        help_text="Текущий баланс пользователя в условных единицах."
    )

    # Уникальные related_name, чтобы не конфликтовать с дефолтными
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='api_users',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='api_user_permissions',
        blank=True,
    )

    def __str__(self):
        return f"{self.username} — баланс: {self.balance:.2f}"

class Dictionary(models.Model):  # Модель для словарей
    owner = models.ForeignKey(User, on_delete=models.CASCADE,related_name='dictionaries') # Владелец словаря
    name = models.CharField(max_length=100)  # Обязательное
    description = models.TextField(blank=True)  # Описание/темы, можно сделать обязательным для продажи
    source_lang = models.CharField(max_length=50) # Язык-источник
    target_lang = models.CharField(max_length=50)  # Язык-перевод
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)  # ← 0.00
    allow_temporary_access = models.BooleanField(default=False)
    temporary_days = models.PositiveIntegerField(default=7, null=True, blank=True)
    is_for_sale = models.BooleanField(default=False)
    cover_image = models.URLField(blank=True)  # Для обратной совместимости
    cover_image_file = models.ImageField(upload_to='dictionaries/covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def clean(self):
        # Валидация перед сохранением
        if self.is_for_sale:
            if not self.name:
                raise ValidationError("Название обязательно для словаря на продажу.")
            if not self.description:  # Или темы, если добавишь отдельное поле
                raise ValidationError("Описание (темы) обязательно для словаря на продажу.")
        super().clean()

class Word(models.Model):  # Модель для слов в словаре
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    example = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.word} -> {self.translation}"

class Purchase(models.Model):  # Новая модель для покупок
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=10, choices=[('permanent', 'Permanent'), ('temporary', 'Temporary')])
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bought {self.dictionary.name}"