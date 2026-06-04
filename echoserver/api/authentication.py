from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from bson import ObjectId
from main.models import User


class CustomJWTAuthentication(JWTAuthentication):
    """Кастомная JWT аутентификация с поддержкой ObjectId"""

    def get_user(self, validated_token):
        """Получает пользователя по _id из токена"""
        user_id = validated_token.get('user_id')
        if not user_id:
            raise AuthenticationFailed('User ID not found in token', code='user_not_found')

        try:
            # Конвертируем строку обратно в ObjectId для поиска
            user = User.objects.get(_id=ObjectId(user_id))
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found', code='user_not_found')
        except Exception as e:
            raise AuthenticationFailed(f'Invalid user ID: {str(e)}', code='invalid_user_id')

        if not user.is_active:
            raise AuthenticationFailed('User is inactive', code='user_inactive')

        return user