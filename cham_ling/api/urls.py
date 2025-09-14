from django.urls import path
from .views import LoginView, DictionaryCreateView, WordCreateView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('dictionaries/create/', DictionaryCreateView.as_view(), name='dictionary_create'),
    path('words/create/', WordCreateView.as_view(), name='word_create'),
]