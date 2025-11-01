"""
Сериализаторы для API endpoints.

Этот модуль содержит все сериализаторы для преобразования
данных между форматами Django models и JSON API responses.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Dictionary, Word, LearningProgress
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.

    Используется для возврата информации о пользователе в API ответах.

    Fields:
        id: Уникальный идентификатор пользователя.
        email: Email пользователя.
    """
    class Meta:
        model = User
        fields = ['id', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля пользователя и настроек.

    Используется для получения и обновления профиля пользователя,
    включая настройки уведомлений.

    Fields:
        id: Уникальный идентификатор пользователя.
        username: Имя пользователя.
        email: Email пользователя.
        balance: Текущий баланс пользователя.
        notifications_enabled: Включены ли уведомления.
        notification_hour: Час для отправки уведомления (0-23).
        notification_minute: Минута для отправки уведомления (0-59).
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'balance',
            'notifications_enabled', 'notification_hour', 'notification_minute'
        ]
        read_only_fields = ['id', 'balance']
        extra_kwargs = {
            'username': {'read_only': True},  # Username обычно не меняется
            'email': {'read_only': True},  # Email можно менять отдельно, если нужно
        }

    def validate_notification_hour(self, value):
        """Проверяет, что час находится в диапазоне 0-23."""
        if not 0 <= value <= 23:
            raise serializers.ValidationError("Час должен быть от 0 до 23.")
        return value

    def validate_notification_minute(self, value):
        """Проверяет, что минута находится в диапазоне 0-59."""
        if not 0 <= value <= 59:
            raise serializers.ValidationError("Минута должна быть от 0 до 59.")
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Обрабатывает данные регистрации и создаёт нового пользователя
    с хешированием пароля.

    Fields:
        username: Имя пользователя (обязательно, уникально).
        email: Email пользователя (обязательно, уникален).
        password: Пароль пользователя (обязательно, write_only).
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        Создаёт нового пользователя с хешированием пароля.

        Args:
            validated_data: Валидированные данные пользователя.

        Returns:
            User: Созданный объект пользователя.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для авторизации пользователя.

    Проверяет учётные данные пользователя и возвращает объект user
    для генерации JWT токенов.

    Fields:
        email: Email пользователя (обязательно).
        password: Пароль пользователя (обязательно).
    """
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        """
        Валидирует учётные данные пользователя.

        Args:
            data: Словарь с email и password.

        Returns:
            dict: Словарь с ключом 'user' и объектом пользователя.

        Raises:
            ValidationError: Если учётные данные неверны.
        """
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError({'email': ['Invalid email or password.']})
        return {'user': user}

class DictionarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Dictionary.

    Преобразует объекты Dictionary в JSON формат с дополнительными
    вычисляемыми полями (cover_image_url, is_owner, word_count, is_purchased).

    Computed Fields:
        cover_image_url: Полный URL обложки (из файла или URL поля).
        is_owner: Является ли текущий пользователь владельцем словаря.
        word_count: Количество слов в словаре.
        is_purchased: Куплен ли словарь текущим пользователем.

    Write Fields:
        cover_image_file: Файл обложки (write_only, загружается в media/dictionaries/covers/).
        cover_image: URL обложки (опционально, для обратной совместимости).
    """
    cover_image_url = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    word_count = serializers.SerializerMethodField()
    is_purchased = serializers.SerializerMethodField()
    
    class Meta:
        model = Dictionary
        fields = [
            'id', 'owner', 'name', 'description', 'source_lang', 'target_lang',
            'price', 'allow_temporary_access', 'temporary_days', 'is_for_sale',
            'cover_image', 'cover_image_file', 'cover_image_url', 'is_owner',
            'word_count', 'is_purchased', 'created_at'
        ]
        extra_kwargs = {
            'owner': {'read_only': True},
            'cover_image_file': {'write_only': True, 'required': False},
        }
    
    def get_cover_image_url(self, obj):
        """
        Возвращает полный URL обложки словаря.

        Приоритет: cover_image_file > cover_image > None.

        Args:
            obj: Объект Dictionary.

        Returns:
            str or None: Полный URL обложки или None.
        """
        if obj.cover_image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image_file.url)
            return obj.cover_image_file.url
        return obj.cover_image if obj.cover_image else None
    
    def get_is_owner(self, obj):
        """
        Проверяет, является ли текущий пользователь владельцем словаря.

        Args:
            obj: Объект Dictionary.

        Returns:
            bool: True, если пользователь владелец, иначе False.
        """
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.owner == request.user
        return False
    
    def get_word_count(self, obj):
        """
        Возвращает количество слов в словаре.

        Args:
            obj: Объект Dictionary.

        Returns:
            int: Количество слов в словаре.
        """
        return obj.words.count()
    
    def get_is_purchased(self, obj):
        """
        Проверяет, куплен ли словарь текущим пользователем.

        Args:
            obj: Объект Dictionary.

        Returns:
            bool: True, если словарь куплен, иначе False.
        """
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            from .models import Purchase
            return Purchase.objects.filter(user=request.user, dictionary=obj).exists()
        return False

    def create(self, validated_data):
        """
        Создаёт новый словарь для текущего пользователя.

        Args:
            validated_data: Валидированные данные словаря.

        Returns:
            Dictionary: Созданный объект словаря.
        """
        request = self.context.get('request')
        return Dictionary.objects.create(owner=request.user, **validated_data)
    
    def update(self, instance, validated_data):
        """
        Обновляет существующий словарь.

        Обновляет только переданные поля, сохраняет остальные без изменений.

        Args:
            instance: Существующий объект Dictionary.
            validated_data: Валидированные данные для обновления.

        Returns:
            Dictionary: Обновлённый объект словаря.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate(self, data):
        """
        Дополнительная валидация на уровне сериализатора.

        Проверяет, что для словарей на продажу указаны обязательные поля.

        Args:
            data: Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            ValidationError: Если для словаря на продажу отсутствуют
                            обязательные поля (name или description).
        """
        if data.get('is_for_sale'):
            if not data.get('name') and not self.instance:
                raise serializers.ValidationError("Название обязательно для словаря на продажу.")
            if not data.get('description') and not self.instance:
                raise serializers.ValidationError("Описание обязательно для словаря на продажу.")
        return data

class WordSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Word.

    Преобразует объекты Word в JSON формат для API ответов.
    При создании слова автоматически связывает его со словарём,
    указанным в dictionary_id из request body.

    Fields:
        id: Уникальный идентификатор слова.
        dictionary: ID словаря (read_only, определяется из request).
        word: Слово на языке-источнике (обязательно).
        translation: Перевод слова (обязательно).
        image_url: URL изображения для слова (опционально).
        example: Пример использования слова (опционально).
    """
    class Meta:
        model = Word
        fields = ['id', 'dictionary', 'word', 'translation', 'image_url', 'example']
        extra_kwargs = {
            'dictionary': {'read_only': True},
        }

    def create(self, validated_data):
        """
        Создаёт новое слово в указанном словаре.

        Получает dictionary_id из request body и проверяет,
        что пользователь является владельцем словаря.

        Args:
            validated_data: Валидированные данные слова.

        Returns:
            Word: Созданный объект слова.

        Raises:
            Dictionary.DoesNotExist: Если словарь не найден.
            PermissionError: Если пользователь не владелец словаря.
        """
        request = self.context.get('request')
        dictionary_id = request.data.get('dictionary_id')
        dictionary = Dictionary.objects.get(id=dictionary_id, owner=request.user)
        validated_data['dictionary'] = dictionary
        return Word.objects.create(**validated_data)


class LearningProgressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для прогресса изучения слов.

    Используется для получения и обновления прогресса пользователя
    по изучению слов в словарях.

    Fields:
        id: Уникальный идентификатор прогресса.
        dictionary: ID словаря.
        learned_words: Массив ID изученных слов.
        learned_words_count: Количество изученных слов (read-only).
        total_words: Общее количество слов в словаре (read-only).
        progress_percentage: Процент изучения (read-only, 0-100).
        last_updated: Дата последнего обновления прогресса.
    """
    learned_words_count = serializers.SerializerMethodField()
    total_words = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = LearningProgress
        fields = [
            'id', 'dictionary', 'learned_words', 'learned_words_count',
            'total_words', 'progress_percentage', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']

    def get_learned_words_count(self, obj):
        """Возвращает количество изученных слов."""
        return obj.learned_words.count()

    def get_total_words(self, obj):
        """Возвращает общее количество слов в словаре."""
        return obj.dictionary.words.count()

    def get_progress_percentage(self, obj):
        """Возвращает процент изученных слов."""
        return obj.get_progress_percentage()

    def create(self, validated_data):
        """
        Создаёт или обновляет прогресс изучения для текущего пользователя.

        Если прогресс уже существует, обновляет его.
        Если нет - создаёт новый.
        """
        request = self.context.get('request')
        user = request.user
        dictionary = validated_data['dictionary']

        # Пытаемся получить существующий прогресс
        progress, created = LearningProgress.objects.get_or_create(
            user=user,
            dictionary=dictionary,
            defaults={}
        )

        # Обновляем изученные слова
        learned_words = validated_data.get('learned_words', [])
        if learned_words:
            progress.learned_words.set(learned_words)

        return progress

    def update(self, instance, validated_data):
        """
        Обновляет прогресс изучения.

        Добавляет или обновляет список изученных слов.
        """
        learned_words = validated_data.get('learned_words', None)
        if learned_words is not None:
            instance.learned_words.set(learned_words)
        
        instance.save()
        return instance