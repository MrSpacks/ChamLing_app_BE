from django.db import models
from django.contrib.auth.models import AbstractUser

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

class Dictionary(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dictionaries')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    source_lang = models.CharField(max_length=50)
    target_lang = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.50)
    is_temporary_access = models.BooleanField(default=False)
    temp_duration_days = models.IntegerField(default=7, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Word(models.Model):
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    example = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.word} -> {self.translation}"

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=10, choices=[('permanent', 'Permanent'), ('temporary', 'Temporary')])
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bought {self.dictionary.name}"