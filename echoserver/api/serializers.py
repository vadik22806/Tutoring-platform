import re
from rest_framework import serializers
from main import models
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
        fields = ['id', 'name', 'level']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'role', 'bio', 'rating', 'subject_ids']
        extra_kwargs = {
            'password': {'write_only': True}
        }


# ========== ВХОДНЫЕ СЕРИАЛИЗАТОРЫ ==========

class RegisterSerializer(serializers.Serializer):
    """Сериализатор для регистрации с валидацией"""
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=['student', 'tutor'])
    bio = serializers.CharField(required=False, allow_blank=True)
    subjects = serializers.ListField(child=serializers.CharField(), required=False, default=[])

    def validate_email(self, value):
        if value and models.User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def validate_phone(self, value):
        if not value:
            return value
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        if models.User.objects.filter(phone=cleaned).exists():
            raise serializers.ValidationError('Пользователь с таким телефоном уже существует')
        return cleaned

    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError('Укажите email или номер телефона')
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError('Пароли не совпадают')
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        subjects = validated_data.pop('subjects', [])
        phone = validated_data.get('phone', None)
        if phone:
            validated_data['phone'] = re.sub(r'[\s\-\(\)]', '', phone)
        
        user = models.User(
            email=validated_data.get('email') or None,
            phone=validated_data.get('phone') or None,
            first_name=validated_data['first_name'],
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role'],
            bio=validated_data.get('bio', ''),
            subject_ids=list(subjects) if subjects else [],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа"""
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=128)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError('Укажите email/телефон и пароль')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Неверный email/телефон или пароль')

        data['user'] = user
        return data


class ProfileUpdateSerializer(serializers.Serializer):
    """Сериализатор для редактирования профиля"""
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    subject_ids = serializers.ListField(child=serializers.CharField(), required=False)

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.pop('instance_user', None)
        super().__init__(*args, **kwargs)

    def validate_email(self, value):
        if value and self.instance_user:
            if models.User.objects.filter(email=value).exclude(pk=self.instance_user.pk).exists():
                raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def validate_phone(self, value):
        if value and self.instance_user:
            cleaned = re.sub(r'[\s\-\(\)]', '', value)
            if models.User.objects.filter(phone=cleaned).exclude(pk=self.instance_user.pk).exists():
                raise serializers.ValidationError('Пользователь с таким телефоном уже существует')
            return cleaned
        return value

    def update_instance(self, user):
        data = self.validated_data
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'bio' in data:
            user.bio = data['bio']
        if 'subject_ids' in data:
            user.subject_ids = list(data['subject_ids'])
        if 'email' in data:
            user.email = data['email'] or None
        if 'phone' in data:
            cleaned = re.sub(r'[\s\-\(\)]', '', data['phone']) if data['phone'] else None
            user.phone = cleaned or None
        user.save()
        return user


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lesson
        fields = ['id', 'tutor_id', 'student_id', 'subject_id', 'date', 'duration', 'price', 'status']
        extra_kwargs = {
            'tutor_id': {'required': False},
            'student_id': {'required': False},
            'status': {'required': False},
        }


class SavedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SavedLesson
        fields = ['id', 'student_id', 'lesson_id', 'added_at']


class BookingGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookingGroup
        fields = ['id', 'student_id', 'created_at', 'total_price', 'lessons_count']