"""
API View классы для обработки HTTP запросов.

Этот модуль содержит все представления (views) для API endpoints:
- Аутентификация (регистрация, логин)
- Управление словарями (CRUD операции)
- Управление словами
- Магазин словарей (marketplace)
- Покупка словарей
"""
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate

from .models import User, Dictionary, Word, Purchase, LearningProgress
from .serializers import (
    LoginSerializer,
    UserSerializer,
    UserProfileSerializer,
    DictionarySerializer,
    WordSerializer,
    RegisterSerializer,
    LearningProgressSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    """
    API endpoint для регистрации новых пользователей.

    Создаёт нового пользователя и возвращает JWT токены (access и refresh)
    для автоматической авторизации после регистрации.

    Methods:
        post(request): Создаёт нового пользователя и возвращает токены.

    Request Body:
        - username: Имя пользователя (обязательно, уникально)
        - email: Email пользователя (обязательно, уникален)
        - password: Пароль пользователя (обязательно)

    Returns:
        - 201 CREATED: Успешная регистрация с токенами
        - 400 BAD_REQUEST: Ошибка валидации (email/username уже существует)

    Permissions:
        AllowAny - доступно всем пользователям.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not email or not password:
            return Response(
                {'detail': 'Username, email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'User with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': 'User with this username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API endpoint для авторизации существующих пользователей.

    Проверяет учётные данные пользователя и возвращает JWT токены
    (access и refresh) для доступа к защищённым API endpoints.

    Methods:
        post(request): Аутентифицирует пользователя и возвращает токены.

    Request Body:
        - email: Email пользователя (обязательно)
        - password: Пароль пользователя (обязательно)

    Returns:
        - 200 OK: Успешный логин с токенами
        - 400 BAD_REQUEST: Неверные учётные данные

    Permissions:
        AllowAny - доступно всем пользователям.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_unsplash_image(query):
    """
    Получает изображение из Unsplash API по запросу.

    Используется для автоматического подбора обложек словарей
    и изображений для слов, если пользователь не загрузил свои.

    Args:
        query (str): Поисковый запрос для изображения (например, "language dictionary").

    Returns:
        str or None: URL изображения или None, если запрос не удался.

    Note:
        Требует настройки UNSPLASH_API_KEY в settings.py.
        При ошибке запроса возвращает None без выбрасывания исключения.
    """
    url = "https://api.unsplash.com/photos/random"
    params = {
        "client_id": settings.UNSPLASH_API_KEY,
        "query": query,
        "orientation": "landscape"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("urls", {}).get("regular")
    except requests.RequestException:
        return None


class DictionaryCreateView(APIView):
    """
    API endpoint для создания нового словаря.

    Создаёт словарь с указанными параметрами. Если не указана обложка,
    автоматически подбирает изображение из Unsplash API.

    Methods:
        post(request): Создаёт новый словарь для текущего пользователя.

    Request Body:
        - name: Название словаря (обязательно)
        - description: Описание словаря
        - source_lang: Язык-источник (обязательно)
        - target_lang: Язык-перевод (обязательно)
        - price: Цена для продажи (по умолчанию 0.00)
        - is_for_sale: Выставить на продажу (по умолчанию False)
        - cover_image: URL обложки (опционально)
        - cover_image_file: Файл обложки (опционально)

    Returns:
        - 201 CREATED: Словарь создан успешно
        - 400 BAD_REQUEST: Ошибка валидации данных

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        
        # Если загружен файл - используем его, иначе проверяем URL
        if request.FILES.get('cover_image_file'):
            # Файл уже в request.FILES, не нужно обрабатывать
            pass
        elif not data.get('cover_image'):
            # Если нет ни файла, ни URL - получаем из Unsplash
            query = data.get('name', 'language dictionary')
            image_url = get_unsplash_image(query)
            if image_url:
                data['cover_image'] = image_url
        
        serializer = DictionarySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        dictionary = serializer.save()
        
        # Возвращаем URL изображения (из файла или URL)
        cover_image_url = None
        if dictionary.cover_image_file:
            cover_image_url = request.build_absolute_uri(dictionary.cover_image_file.url)
        elif dictionary.cover_image:
            cover_image_url = dictionary.cover_image
            
        return Response({
            'id': dictionary.id,
            'name': dictionary.name,
            'cover_image': cover_image_url or dictionary.cover_image,
            'cover_image_url': cover_image_url
        }, status=status.HTTP_201_CREATED)


class WordCreateView(APIView):
    """
    API endpoint для добавления слова в словарь.

    Создаёт новое слово с переводом в указанном словаре.
    Если не указано изображение, автоматически подбирает из Unsplash.

    Methods:
        post(request): Добавляет слово в словарь.

    Request Body:
        - dictionary_id: ID словаря (обязательно, в теле запроса)
        - word: Слово на языке-источнике (обязательно)
        - translation: Перевод слова (обязательно)
        - image_url: URL изображения для слова (опционально)
        - example: Пример использования (опционально)

    Returns:
        - 201 CREATED: Слово добавлено успешно
        - 400 BAD_REQUEST: Ошибка валидации данных
        - 403 FORBIDDEN: Пользователь не владелец словаря

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = request.data.copy()
        if not data.get('image_url'):
            query = data.get('word', 'language')
            image_url = get_unsplash_image(query)
            if image_url:
                data['image_url'] = image_url
        serializer = WordSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        word = serializer.save()
        return Response({
            'id': word.id,
            'word': word.word,
            'translation': word.translation,
            'image_url': word.image_url
        }, status=status.HTTP_201_CREATED)


class DictionaryListView(APIView):
    """
    API endpoint для получения списка словарей пользователя.

    Возвращает все словари, к которым у пользователя есть доступ:
    - Словари, созданные пользователем (owner)
    - Словари, купленные пользователем (purchased)

    Methods:
        get(request): Возвращает список словарей пользователя.

    Returns:
        - 200 OK: Список словарей пользователя

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Получаем словари, где пользователь является владельцем
        owned_dictionaries = Dictionary.objects.filter(owner=request.user)
        
        # Получаем словари, которые пользователь купил
        purchased_dictionaries_ids = Purchase.objects.filter(
            user=request.user
        ).values_list('dictionary_id', flat=True)
        purchased_dictionaries = Dictionary.objects.filter(id__in=purchased_dictionaries_ids)
        
        # Объединяем оба списка (используем distinct чтобы избежать дубликатов)
        all_dictionaries = (owned_dictionaries | purchased_dictionaries).distinct()
        
        serializer = DictionarySerializer(all_dictionaries, many=True, context={'request': request})
        return Response(serializer.data)


class MarketplaceView(APIView):
    """
    API endpoint для получения списка словарей в магазине.

    Возвращает все словари, выставленные на продажу (is_for_sale=True).
    Доступен публично, но если пользователь авторизован,
    в ответе указывается is_owner для каждого словаря.

    Methods:
        get(request): Возвращает список словарей на продажу.

    Returns:
        - 200 OK: Список словарей в магазине

    Permissions:
        AllowAny - доступно всем пользователям (публичный endpoint).
        Поддерживает опциональную JWT аутентификацию для определения is_owner.
    """
    permission_classes = [AllowAny]  # Публичный доступ
    authentication_classes = [JWTAuthentication]  # Поддерживаем аутентификацию для определения is_owner

    def get(self, request):
        dictionaries = Dictionary.objects.filter(is_for_sale=True)
        # Передаем request в context для определения is_owner даже если пользователь не залогинен
        serializer = DictionarySerializer(dictionaries, many=True, context={'request': request})
        return Response(serializer.data)


class DictionaryDetailView(APIView):
    """
    API endpoint для получения, обновления и удаления словаря.

    Предоставляет детальную информацию о словаре и позволяет
    владельцу обновлять и удалять свои словари.

    Methods:
        get(request, pk): Получить детали словаря.
        put(request, pk): Обновить словарь (только владелец).
        delete(request, pk): Удалить словарь (только владелец).

    Returns:
        GET:
        - 200 OK: Детали словаря
        - 403 FORBIDDEN: Нет доступа к словарю
        - 404 NOT_FOUND: Словарь не найден

        PUT:
        - 200 OK: Словарь обновлён
        - 403 FORBIDDEN: Пользователь не владелец
        - 404 NOT_FOUND: Словарь не найден

        DELETE:
        - 204 NO_CONTENT: Словарь удалён
        - 403 FORBIDDEN: Пользователь не владелец
        - 404 NOT_FOUND: Словарь не найден

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Получить детали словаря"""
        try:
            dictionary = Dictionary.objects.get(pk=pk)
            # Пользователь может видеть только свои словари
            if dictionary.owner != request.user:
                # Проверяем покупки
                from .models import Purchase
                if not Purchase.objects.filter(user=request.user, dictionary=dictionary).exists():
                    return Response(
                        {'detail': 'You do not have access to this dictionary.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = DictionarySerializer(dictionary, context={'request': request})
            return Response(serializer.data)
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        """Обновить словарь (только владелец)"""
        try:
            dictionary = Dictionary.objects.get(pk=pk)
            if dictionary.owner != request.user:
                return Response(
                    {'detail': 'You can only update your own dictionaries.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            data = request.data.copy()
            
            # Обработка файла изображения
            if request.FILES.get('cover_image_file'):
                pass  # Файл уже в request.FILES
            elif not data.get('cover_image') and not dictionary.cover_image_file:
                # Если нет изображения - получаем из Unsplash
                query = data.get('name', dictionary.name)
                image_url = get_unsplash_image(query)
                if image_url:
                    data['cover_image'] = image_url
            
            serializer = DictionarySerializer(dictionary, data=data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            updated_dict = serializer.save()
            
            # Возвращаем URL изображения
            cover_image_url = None
            if updated_dict.cover_image_file:
                cover_image_url = request.build_absolute_uri(updated_dict.cover_image_file.url)
            elif updated_dict.cover_image:
                cover_image_url = updated_dict.cover_image
            
            return Response({
                'id': updated_dict.id,
                'name': updated_dict.name,
                'cover_image_url': cover_image_url
            })
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        """Удалить словарь (только владелец)"""
        try:
            dictionary = Dictionary.objects.get(pk=pk)
            if dictionary.owner != request.user:
                return Response(
                    {'detail': 'You can only delete your own dictionaries.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            dictionary.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class DictionaryWordsView(APIView):
    """
    API endpoint для получения списка слов в словаре.

    Возвращает все слова указанного словаря. Доступ к словам имеют:
    - Владелец словаря (owner)
    - Пользователи, купившие словарь (purchased)

    Methods:
        get(request, pk): Возвращает список слов словаря.

    Args:
        pk (int): ID словаря.

    Returns:
        - 200 OK: Список слов словаря
        - 403 FORBIDDEN: Нет доступа к словарю
        - 404 NOT_FOUND: Словарь не найден

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Получить слова словаря"""
        try:
            dictionary = Dictionary.objects.get(pk=pk)
            # Пользователь может видеть слова только своих словарей или купленных
            if dictionary.owner != request.user:
                from .models import Purchase
                if not Purchase.objects.filter(user=request.user, dictionary=dictionary).exists():
                    return Response(
                        {'detail': 'You do not have access to this dictionary.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            words = Word.objects.filter(dictionary=dictionary)
            serializer = WordSerializer(words, many=True)
            return Response(serializer.data)
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class PurchaseDictionaryView(APIView):
    """
    API endpoint для покупки словаря.

    Обрабатывает покупку словаря другим пользователем.
    Симуляция платежа через код 1013 (для демонстрации).

    Methods:
        post(request, pk): Покупает словарь для текущего пользователя.

    Args:
        pk (int): ID словаря для покупки.

    Request Body:
        - payment_code: Код оплаты (обязательно, должен быть "1013")
        - access_type: Тип доступа - 'permanent' или 'temporary' (по умолчанию 'permanent')

    Returns:
        - 201 CREATED: Словарь куплен успешно
        - 400 BAD_REQUEST: Ошибка валидации (неверный код, словарь уже куплен и т.д.)
        - 404 NOT_FOUND: Словарь не найден

    Validations:
        - Словарь должен быть на продажу (is_for_sale=True)
        - Пользователь не должен быть владельцем словаря
        - Словарь не должен быть уже куплен пользователем
        - Код оплаты должен быть "1013"

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Купить словарь (симуляция через код 1013)"""
        try:
            dictionary = Dictionary.objects.get(pk=pk)
            
            # Сначала проверяем код оплаты (ранняя валидация)
            payment_code = request.data.get('payment_code')
            
            if not payment_code:
                return Response(
                    {'detail': 'Payment code is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if payment_code != '1013':
                return Response(
                    {'detail': 'Invalid payment code. Please enter 1013.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, что словарь на продажу
            if not dictionary.is_for_sale:
                return Response(
                    {'detail': 'This dictionary is not for sale.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, что пользователь не владелец
            if dictionary.owner == request.user:
                return Response(
                    {'detail': 'You cannot buy your own dictionary.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, не куплен ли уже словарь
            if Purchase.objects.filter(user=request.user, dictionary=dictionary).exists():
                return Response(
                    {'detail': 'You have already purchased this dictionary.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Определяем тип доступа (permanent или temporary)
            access_type = request.data.get('access_type', 'permanent')
            
            if access_type not in ['permanent', 'temporary']:
                access_type = 'permanent'
            
            # Создаем покупку
            purchase = Purchase.objects.create(
                user=request.user,
                dictionary=dictionary,
                access_type=access_type
            )
            
            return Response({
                'id': purchase.id,
                'dictionary_id': dictionary.id,
                'dictionary_name': dictionary.name,
                'access_type': purchase.access_type,
                'purchased_at': purchase.purchased_at,
                'message': 'Dictionary purchased successfully!'
            }, status=status.HTTP_201_CREATED)
            
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    """
    API endpoint для получения и обновления профиля пользователя.

    Позволяет получить информацию о текущем пользователе и обновить
    настройки уведомлений (включить/выключить, установить время).

    Methods:
        get(request): Получить профиль текущего пользователя.
        put(request): Обновить профиль и настройки пользователя.

    Request Body (PUT):
        - notifications_enabled: Включить/выключить уведомления (bool)
        - notification_hour: Час для уведомления (0-23, int)
        - notification_minute: Минута для уведомления (0-59, int)

    Returns:
        GET:
        - 200 OK: Профиль пользователя

        PUT:
        - 200 OK: Обновлённый профиль пользователя
        - 400 BAD_REQUEST: Ошибка валидации данных

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получить профиль текущего пользователя.

        Returns:
            Response: Профиль пользователя с настройками уведомлений.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """
        Обновить настройки профиля текущего пользователя.

        Позволяет обновить настройки уведомлений (enabled, hour, minute).
        Остальные поля (username, email, balance) доступны только для чтения.

        Returns:
            Response: Обновлённый профиль пользователя или ошибка валидации.
        """
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LearningProgressView(APIView):
    """
    API endpoint для получения и обновления прогресса изучения слов.

    Позволяет получить текущий прогресс пользователя по словарю,
    сохранить прогресс (изученные слова) и синхронизировать между устройствами.

    Methods:
        get(request, dictionary_id): Получить прогресс по словарю.
        post(request, dictionary_id): Сохранить прогресс изучения (создать или обновить).
        put(request, dictionary_id): Обновить прогресс изучения.

    Request Body (POST/PUT):
        - learned_words: Массив ID изученных слов (обязательно, список чисел)

    Returns:
        GET:
        - 200 OK: Прогресс пользователя по словарю
        - 404 NOT_FOUND: Прогресс не найден (можно создать через POST)

        POST/PUT:
        - 200 OK или 201 CREATED: Сохранённый прогресс
        - 400 BAD_REQUEST: Ошибка валидации данных
        - 403 FORBIDDEN: Нет доступа к словарю

    Permissions:
        IsAuthenticated - требуется авторизация.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, dictionary_id):
        """
        Получить прогресс изучения словаря для текущего пользователя.

        Returns:
            Response: Прогресс пользователя или пустой объект если прогресс не найден.
        """
        try:
            dictionary = Dictionary.objects.get(pk=dictionary_id)
            
            # Проверяем доступ к словарю
            if dictionary.owner != request.user:
                from .models import Purchase
                if not Purchase.objects.filter(user=request.user, dictionary=dictionary).exists():
                    return Response(
                        {'detail': 'You do not have access to this dictionary.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Получаем или создаём прогресс
            progress, created = LearningProgress.objects.get_or_create(
                user=request.user,
                dictionary=dictionary,
                defaults={}
            )
            
            serializer = LearningProgressSerializer(progress)
            return Response(serializer.data)
            
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, dictionary_id):
        """
        Сохранить прогресс изучения словаря (создать или обновить).

        Args:
            dictionary_id: ID словаря.

        Returns:
            Response: Сохранённый прогресс изучения.
        """
        try:
            dictionary = Dictionary.objects.get(pk=dictionary_id)
            
            # Проверяем доступ к словарю
            if dictionary.owner != request.user:
                from .models import Purchase
                if not Purchase.objects.filter(user=request.user, dictionary=dictionary).exists():
                    return Response(
                        {'detail': 'You do not have access to this dictionary.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Получаем или создаём прогресс
            progress, created = LearningProgress.objects.get_or_create(
                user=request.user,
                dictionary=dictionary,
                defaults={}
            )
            
            # Обновляем данные
            data = request.data.copy()
            data['dictionary'] = dictionary.id
            
            serializer = LearningProgressSerializer(
                progress,
                data=data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
                return Response(serializer.data, status=status_code)
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Dictionary.DoesNotExist:
            return Response(
                {'detail': 'Dictionary not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, dictionary_id):
        """
        Обновить прогресс изучения словаря.

        Args:
            dictionary_id: ID словаря.

        Returns:
            Response: Обновлённый прогресс изучения.
        """
        return self.post(request, dictionary_id)