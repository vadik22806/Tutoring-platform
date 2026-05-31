from djongo import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from bson import ObjectId


class Subject(models.Model):
    """Модель предмета"""
    _id = models.ObjectIdField(primary_key=True, db_column='_id')
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    level = models.JSONField(default=list, blank=True, verbose_name='Уровни')

    class Meta:
        db_table = "subjects"
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'

    @property
    def id(self):
        return str(self._id) if self._id else ''

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Менеджер пользователей с поддержкой входа по email или телефону"""

    def get_by_natural_key(self, username):
        """Поиск пользователя для аутентификации по email или телефону"""
        try:
            return self.get(email=username)
        except User.DoesNotExist:
            return self.get(phone=username)

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email and not phone:
            raise ValueError('Необходимо указать email или номер телефона')

        # Нормализуем email если он есть
        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        """Создание суперпользователя (админа)"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if not email and not phone:
            raise ValueError('Суперпользователь должен иметь email или телефон')

        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Единая модель пользователя с поддержкой входа по email или телефону"""

    _id = models.ObjectIdField(primary_key=True, db_column='_id')
    # Пароль хранится в защищенном виде благодаря наследованию от AbstractBaseUser
    # Django автоматически хеширует пароль через set_password()
    password = models.CharField(max_length=128, verbose_name='Пароль')
    # Основные поля
    role = models.CharField(max_length=20, choices=[
        ('student', 'Ученик'),
        ('tutor', 'Репетитор'),
        ('admin', 'Администратор')
    ], verbose_name='Роль')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, blank=True, verbose_name='Фамилия')

    # Телефон с валидацией
    phone_regex = RegexValidator(
        regex=r'^\+?[0-9]{10,15}$',
        message='Телефон должен быть в формате: +79991234567 или 89991234567 (10-15 цифр)'
    )
    phone = models.CharField(
        max_length=20,
        validators=[phone_regex],
        unique=True,
        null=True,
        blank=True,
        verbose_name='Телефон'
    )

    subject_ids = models.JSONField(blank=True, default=list, verbose_name='ID предметов')
    rating = models.FloatField(null=True, blank=True, verbose_name='Рейтинг')
    bio = models.TextField(blank=True, verbose_name='О себе')

    # Поля для авторизации
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='Email'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    # Для Django - добавляем related_name чтобы избежать конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    # Для Django
    USERNAME_FIELD = 'email'  # Django требует поле для логина
    REQUIRED_FIELDS = ['first_name', 'role']

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]

    @property
    def id(self):
        return str(self._id) if self._id else ''

    def get_username(self):
        """Возвращает username для аутентификации"""
        return self.email or self.phone

    def clean(self):
        """Валидация модели"""
        if not self.email and not self.phone:
            from django.core.exceptions import ValidationError
            raise ValidationError('Пользователь должен иметь email или номер телефона')

    def save(self, *args, **kwargs):
        # Очищаем телефон от лишних символов перед сохранением
        if self.phone:
            import re
            self.phone = re.sub(r'[\s\-\(\)]', '', self.phone)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.email:
            return f"{self.first_name} {self.last_name} ({self.email})"
        else:
            return f"{self.first_name} {self.last_name} ({self.phone})"


class Lesson(models.Model):
    """Модель занятия"""
    _id = models.ObjectIdField(primary_key=True, db_column='_id')
    tutor_id = models.CharField(max_length=24, verbose_name='ID репетитора')
    student_id = models.CharField(max_length=24, null=True, blank=True, verbose_name='ID ученика')
    subject_id = models.CharField(max_length=24, verbose_name='ID предмета')
    date = models.DateTimeField(verbose_name='Дата и время')
    duration = models.IntegerField(verbose_name='Длительность (мин)')
    price = models.IntegerField(verbose_name='Цена (руб)')
    status = models.CharField(max_length=20, choices=[
        ('available', 'Доступно'),
        ('booked', 'Забронировано'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено')
    ], default='available', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = "lessons"
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        indexes = [
            models.Index(fields=['tutor_id']),
            models.Index(fields=['student_id']),
            models.Index(fields=['date']),
            models.Index(fields=['status', 'date']),
        ]

    @property
    def id(self):
        return str(self._id) if self._id else ''

    def __str__(self):
        return f"Занятие {self.subject_id} на {self.date}"


# ========== НОВАЯ МОДЕЛЬ ДЛЯ ОТЛОЖЕННЫХ ЗАНЯТИЙ ==========

class SavedLesson(models.Model):
    """Модель для отложенных занятий (аналог корзины)"""
    _id = models.ObjectIdField(primary_key=True, db_column='_id')
    student_id = models.CharField(max_length=24, verbose_name='ID ученика')
    lesson_id = models.CharField(max_length=24, verbose_name='ID занятия')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        db_table = "saved_lessons"
        verbose_name = 'Отложенное занятие'
        verbose_name_plural = 'Отложенные занятия'
        # Уникальность: ученик может отложить одно занятие только один раз
        unique_together = ('student_id', 'lesson_id')
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['lesson_id']),
        ]

    @property
    def id(self):
        return str(self._id) if self._id else ''

    def __str__(self):
        return f"Ученик {self.student_id} отложил занятие {self.lesson_id}"


# НОВАЯ МОДЕЛЬ ДЛЯ ГРУППОВЫХ ЗАПИСЕЙ (

class BookingGroup(models.Model):
    """Модель для группировки записей (история заказов)"""
    _id = models.ObjectIdField(primary_key=True, db_column='_id')
    student_id = models.CharField(max_length=24, verbose_name='ID ученика')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оформления')
    total_price = models.IntegerField(verbose_name='Общая стоимость', default=0)
    lessons_count = models.IntegerField(verbose_name='Количество занятий', default=0)

    class Meta:
        db_table = "booking_groups"
        verbose_name = 'Группа записей'
        verbose_name_plural = 'Группы записей'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_id']),
        ]

    @property
    def id(self):
        return str(self._id) if self._id else ''

    def __str__(self):
        return f"Заказ {self.id} от {self.created_at.strftime('%d.%m.%Y')}"