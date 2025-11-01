"""
URL конфигурация для проекта ChamLing.

Определяет маршруты для всех URL паттернов приложения:
- Django admin панель (/admin/)
- API endpoints (/api/)
- Медиа файлы (только в режиме разработки)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin панель для управления данными
    path('admin/', admin.site.urls),
    # API endpoints - все API маршруты определены в api/urls.py
    path('api/', include('api.urls')),
]

# Обслуживание медиафайлов (загруженные пользователями изображения)
# Работает только в режиме разработки (DEBUG=True)
# В продакшене медиа файлы должны обслуживаться веб-сервером (nginx/Apache)
# или через CDN (CloudFront, CloudFlare)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)