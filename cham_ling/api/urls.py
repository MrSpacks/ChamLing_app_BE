from django.urls import path
from .views import LoginView, RegisterView, DictionaryCreateView, WordCreateView, DictionaryListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # 👈 добавили регистрацию
    path('login/', LoginView.as_view(), name='login'),
    path('dictionaries/create/', DictionaryCreateView.as_view(), name='dictionary_create'),
    path('words/create/', WordCreateView.as_view(), name='word_create'),
    path('dictionaries/', DictionaryListView.as_view(), name='dictionary_list'),
]