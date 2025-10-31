from django.urls import path
from .views import (
    LoginView, RegisterView, DictionaryCreateView, WordCreateView, 
    DictionaryListView, MarketplaceView, DictionaryDetailView, DictionaryWordsView
)
from rest_framework_simplejwt.views import TokenObtainPairView , TokenRefreshView


urlpatterns = [
   path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('dictionaries/create/', DictionaryCreateView.as_view(), name='dictionary_create'),
    path('dictionaries/<int:pk>/', DictionaryDetailView.as_view(), name='dictionary_detail'),
    path('dictionaries/<int:pk>/words/', DictionaryWordsView.as_view(), name='dictionary_words'),
    path('words/create/', WordCreateView.as_view(), name='word_create'),
    path('dictionaries/', DictionaryListView.as_view(), name='dictionary_list'),
    path('marketplace/', MarketplaceView.as_view(), name='marketplace'),
]