"""
Модели данных для приложения ChamLing.

Этот модуль содержит все модели данных для работы со словарями,
пользователями, словами и покупками.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    Расширенная модель пользователя с балансом.

    Наследуется от AbstractUser Django и добавляет поле balance
    для будущей реализации системы платежей и покупок словарей.

    Attributes:
        balance: Текущий баланс пользователя в условных единицах.
                 Максимальное значение: 9,999,999.99

    Note:
        Используются уникальные related_name для groups и user_permissions,
        чтобы избежать конфликтов с дефолтными полями Django.
    """
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Текущий баланс пользователя в условных единицах."
    )

    # Настройки уведомлений
    notifications_enabled = models.BooleanField(
        default=False,
        help_text="Включены ли уведомления для напоминания об учёбе."
    )
    notification_hour = models.IntegerField(
        default=9,
        help_text="Час для отправки уведомления (0-23)."
    )
    notification_minute = models.IntegerField(
        default=0,
        help_text="Минута для отправки уведомления (0-59)."
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
        """Возвращает строковое представление пользователя с балансом."""
        return f"{self.username} — баланс: {self.balance:.2f}"


class Dictionary(models.Model):
    """
    Модель словаря для изучения языков.

    Представляет собой коллекцию слов с переводами между двумя языками.
    Словарь может быть создан пользователем, выложен на продажу,
    и содержать множество слов.

    Attributes:
        owner: Владелец словаря (ForeignKey к User).
        name: Название словаря (обязательное поле, max_length=100).
        description: Описание словаря и темы (обязательно для продажи).
        source_lang: Язык-источник (код языка, max_length=50).
        target_lang: Язык-перевод (код языка, max_length=50).
        price: Цена словаря для продажи (max 9999.99).
        allow_temporary_access: Разрешён ли временный доступ к словарю.
        temporary_days: Количество дней временного доступа (по умолчанию 7).
        is_for_sale: Выставлен ли словарь на продажу.
        cover_image: URL обложки словаря (для обратной совместимости).
        cover_image_file: Файл обложки (загружается в media/dictionaries/covers/).
        created_at: Дата создания словаря (автоматически).

    Note:
        При выставлении на продажу (is_for_sale=True) обязательно
        должны быть указаны name и description.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dictionaries'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    source_lang = models.CharField(max_length=50)
    target_lang = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    allow_temporary_access = models.BooleanField(default=False)
    temporary_days = models.PositiveIntegerField(default=7, null=True, blank=True)
    is_for_sale = models.BooleanField(default=False)
    cover_image = models.URLField(blank=True)  # Для обратной совместимости
    cover_image_file = models.ImageField(upload_to='dictionaries/covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Возвращает название словаря."""
        return self.name

    def clean(self):
        """
        Валидация словаря перед сохранением.

        Проверяет, что для словарей на продажу указаны
        обязательные поля: name и description.

        Raises:
            ValidationError: Если словарь на продажу, но отсутствуют
                            обязательные поля.
        """
        if self.is_for_sale:
            if not self.name:
                raise ValidationError("Название обязательно для словаря на продажу.")
            if not self.description:
                raise ValidationError("Описание (темы) обязательно для словаря на продажу.")
        super().clean()


class Word(models.Model):
    """
    Модель слова в словаре.

    Представляет одно слово с переводом, связанное с конкретным словарём.

    Attributes:
        dictionary: Словарь, к которому относится слово (ForeignKey к Dictionary).
        word: Слово на языке-источнике (max_length=100).
        translation: Перевод слова на целевом языке (max_length=100).
        image_url: URL изображения для визуализации слова.
        example: Пример использования слова в предложении.
        created_at: Дата добавления слова (автоматически).

    Related:
        Доступ к словам словаря: dictionary.words.all()
    """
    dictionary = models.ForeignKey(
        Dictionary,
        on_delete=models.CASCADE,
        related_name='words'
    )
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    example = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Возвращает строковое представление слова и перевода."""
        return f"{self.word} -> {self.translation}"


class Purchase(models.Model):
    """
    Модель покупки словаря пользователем.

    Хранит информацию о приобретении словаря другим пользователем,
    включая тип доступа (постоянный или временный).

    Attributes:
        user: Пользователь, который купил словарь (ForeignKey к User).
        dictionary: Купленный словарь (ForeignKey к Dictionary).
        access_type: Тип доступа - 'permanent' (постоянный) или 'temporary' (временный).
        purchased_at: Дата и время покупки (автоматически при создании).

    Choices:
        access_type может быть:
        - 'permanent': Постоянный доступ к словарю.
        - 'temporary': Временный доступ (срок определяется словарём).
    """
    ACCESS_CHOICES = [
        ('permanent', 'Permanent'),
        ('temporary', 'Temporary')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=10, choices=ACCESS_CHOICES)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Метаданные модели."""
        verbose_name = "Покупка"
        verbose_name_plural = "Покупки"

    def __str__(self):
        """Возвращает строковое представление покупки."""
        return f"{self.user.username} bought {self.dictionary.name}"


class LearningProgress(models.Model):
    """
    Модель прогресса изучения слов пользователем.

    Хранит информацию о том, какие слова пользователь уже изучил
    в каждом словаре. Позволяет синхронизировать прогресс между устройствами.

    Attributes:
        user: Пользователь, который изучает слова (ForeignKey к User).
        dictionary: Словарь, в котором изучаются слова (ForeignKey к Dictionary).
        learned_words: Множество ID изученных слов (ManyToMany к Word).
        last_updated: Дата последнего обновления прогресса (автоматически).

    Note:
        Используется уникальное ограничение (user, dictionary) чтобы
        у каждого пользователя был только один объект прогресса на словарь.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_progress')
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='learning_progress')
    learned_words = models.ManyToManyField(Word, related_name='learned_by_users', blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        """Метаданные модели."""
        verbose_name = "Прогресс изучения"
        verbose_name_plural = "Прогресс изучения"
        unique_together = [['user', 'dictionary']]
        indexes = [
            models.Index(fields=['user', 'dictionary']),
        ]

    def __str__(self):
        """Возвращает строковое представление прогресса."""
        learned_count = self.learned_words.count()
        return f"{self.user.username} - {self.dictionary.name}: {learned_count} слов изучено"

    def get_progress_percentage(self):
        """
        Вычисляет процент изученных слов в словаре.

        Returns:
            int: Процент изученных слов (0-100).
        """
        total_words = self.dictionary.words.count()
        if total_words == 0:
            return 0
        learned_count = self.learned_words.count()
        return round((learned_count / total_words) * 100)