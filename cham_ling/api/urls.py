"""
URL маршруты для API endpoints.

Все URL начинаются с префикса /api/ (определён в cham_ling/urls.py).

Маршруты:
    - Аутентификация: /api/auth/register/, /api/auth/login/, /api/auth/refresh/
    - Словари: /api/dictionaries/, /api/dictionaries/<id>/, /api/dictionaries/create/
    - Слова: /api/words/create/, /api/dictionaries/<id>/words/
    - Магазин: /api/marketplace/
    - Покупки: /api/dictionaries/<id>/purchase/
"""
from django.urls import path
from .views import (
    LoginView, RegisterView, DictionaryCreateView, WordCreateView, 
    DictionaryListView, MarketplaceView, DictionaryDetailView, DictionaryWordsView,
    PurchaseDictionaryView, UserProfileView, LearningProgressView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    # Аутентификация
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Профиль пользователя
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),

    # Словари - CRUD операции
    path('dictionaries/create/', DictionaryCreateView.as_view(), name='dictionary_create'),
    path('dictionaries/<int:pk>/', DictionaryDetailView.as_view(), name='dictionary_detail'),
    path('dictionaries/<int:pk>/words/', DictionaryWordsView.as_view(), name='dictionary_words'),
    path('dictionaries/<int:pk>/purchase/', PurchaseDictionaryView.as_view(), name='purchase_dictionary'),
    path('dictionaries/', DictionaryListView.as_view(), name='dictionary_list'),

    # Слова
    path('words/create/', WordCreateView.as_view(), name='word_create'),

    # Прогресс изучения
    path('dictionaries/<int:dictionary_id>/progress/', LearningProgressView.as_view(), name='learning_progress'),

    # Магазин (публичный endpoint)
    path('marketplace/', MarketplaceView.as_view(), name='marketplace'),
]