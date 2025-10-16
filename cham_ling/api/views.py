import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

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
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        self.token_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(self.token_data, status=status.HTTP_201_CREATED)


# -------------------------------
# Логин
# -------------------------------
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


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