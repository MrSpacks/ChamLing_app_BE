from django.urls import path
from .views import LoginView, RegisterView, DictionaryCreateView, WordCreateView, DictionaryListView
from rest_framework_simplejwt.views import TokenObtainPairView , TokenRefreshView


urlpatterns = [
   path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('dictionaries/create/', DictionaryCreateView.as_view(), name='dictionary_create'),
    path('words/create/', WordCreateView.as_view(), name='word_create'),
    path('dictionaries/', DictionaryListView.as_view(), name='dictionary_list'),
]