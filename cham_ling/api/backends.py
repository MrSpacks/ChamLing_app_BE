"""
Кастомные бэкенды аутентификации.

Этот модуль содержит дополнительные способы аутентификации пользователей.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailAuthBackend(ModelBackend):
    """
    Бэкенд аутентификации по email вместо username.

    Позволяет пользователям входить в систему, используя email и password,
    вместо стандартного username/password Django.

    Используется в AUTHENTICATION_BACKENDS в settings.py.

    Args:
        request: HTTP request объект.
        email (str): Email пользователя для аутентификации.
        password (str): Пароль пользователя.
        **kwargs: Дополнительные параметры.

    Returns:
        User or None: Объект пользователя при успешной аутентификации,
                      None если аутентификация не удалась.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
        return None