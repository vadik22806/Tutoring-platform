from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User


class EmailOrPhoneBackend(ModelBackend):
    """Бэкенд для аутентификации по email ИЛИ телефону"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Ищем пользователя по email ИЛИ телефону
            user = User.objects.get(
                Q(email=username) | Q(phone=username)
            )

            # Проверяем пароль
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None