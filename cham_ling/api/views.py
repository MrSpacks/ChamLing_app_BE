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




from .models import User, Dictionary, Word
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
        if not data.get('cover_image'):
            query = data.get('name', 'language dictionary')
            image_url = get_unsplash_image(query)
            if image_url:
                data['cover_image'] = image_url
        serializer = DictionarySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        dictionary = serializer.save()
        return Response({
            'id': dictionary.id,
            'name': dictionary.name,
            'cover_image': dictionary.cover_image
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
        dictionaries = Dictionary.objects.filter(owner=request.user)
        serializer = DictionarySerializer(dictionaries, many=True)
        return Response(serializer.data)