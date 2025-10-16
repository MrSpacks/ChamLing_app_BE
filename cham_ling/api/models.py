from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
class User(AbstractUser):
    # Добавляем уникальные related_name для групп и разрешений
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='chamling_users',  # Уникальное имя, например, 'chamling_users'
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='chamling_user_permissions',  # Уникальное имя, например, 'chamling_user_permissions'
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class Dictionary(models.Model):  # Модель для словарей
    owner = models.ForeignKey(User, on_delete=models.CASCADE,related_name='dictionaries') # Владелец словаря
    name = models.CharField(max_length=100)  # Обязательное
    description = models.TextField(blank=True)  # Описание/темы, можно сделать обязательным для продажи
    source_lang = models.CharField(max_length=50) # Язык-источник
    target_lang = models.CharField(max_length=50) # Язык-перевод
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.50)
    is_temporary_access = models.BooleanField(default=False)
    temp_duration_days = models.IntegerField(default=7, null=True, blank=True)
    is_for_sale = models.BooleanField(default=False)  # Новый флаг: на продажу или нет
    cover_image = models.URLField(blank=True)  # Обложка (URL, можно из S3/Unsplash)
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