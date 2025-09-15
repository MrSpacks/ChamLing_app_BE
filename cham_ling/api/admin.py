from django.contrib import admin
from .models import User, Dictionary, Word, Purchase

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')  # Поля для отображения

@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'price', 'is_for_sale', 'created_at')  # Поля для отображения
    list_filter = ('is_for_sale', 'source_lang', 'target_lang')  # Фильтры
    search_fields = ('name', 'description')  # Поиск

admin.site.register(Word)
admin.site.register(Purchase)