import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate




from .models import User, Dictionary, Word, Purchase
from .serializers import (
    LoginSerializer,
    UserSerializer,
    DictionarySerializer,
    WordSerializer,
    RegisterSerializer,
)

# -------------------------------
# Регистрация с JWT-авторизацией
# -------------------------------

User = get_user_model()

class RegisterView(APIView):
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

# -------------------------------
# Логин
# -------------------------------
class LoginView(APIView):
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




# -------------------------------
# Подбор изображения для словаря
# -------------------------------
def get_unsplash_image(query):
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


# -------------------------------
# Создание словаря
# -------------------------------
class DictionaryCreateView(APIView):
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


# -------------------------------
# Добавление слова
# -------------------------------
class WordCreateView(APIView):
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


# -------------------------------
# Список словарей
# -------------------------------
class DictionaryListView(APIView):
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


# -------------------------------
# Marketplace - словари на продажу
# -------------------------------
class MarketplaceView(APIView):
    permission_classes = [AllowAny]  # Публичный доступ
    authentication_classes = [JWTAuthentication]  # Поддерживаем аутентификацию для определения is_owner

    def get(self, request):
        dictionaries = Dictionary.objects.filter(is_for_sale=True)
        # Передаем request в context для определения is_owner даже если пользователь не залогинен
        serializer = DictionarySerializer(dictionaries, many=True, context={'request': request})
        return Response(serializer.data)


# -------------------------------
# Детали словаря, обновление, удаление
# -------------------------------
class DictionaryDetailView(APIView):
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


# -------------------------------
# Слова словаря
# -------------------------------
class DictionaryWordsView(APIView):
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


# -------------------------------
# Покупка словаря
# -------------------------------
class PurchaseDictionaryView(APIView):
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