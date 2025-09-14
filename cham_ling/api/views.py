from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Dictionary, Word
from .serializers import LoginSerializer, UserSerializer, DictionarySerializer, WordSerializer

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

class DictionaryCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DictionarySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        dictionary = serializer.save()
        return Response({'id': dictionary.id, 'name': dictionary.name}, status=status.HTTP_201_CREATED)

class WordCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        word = serializer.save()
        return Response({'id': word.id, 'word': word.word, 'translation': word.translation}, status=status.HTTP_201_CREATED)