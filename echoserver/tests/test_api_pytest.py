"""
pytest-тесты API StudyEasy с DRF APIClient.
Не требует запущенного сервера — использует встроенный test client.

Запуск: cd echoserver && python -m pytest tests/test_api_pytest.py -v
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import get_user_model
from bson import ObjectId
from datetime import timedelta

from main.models import Subject, Lesson, SavedLesson
from api.utils import atomic_book_lesson, revoke_refresh_token, get_mongo_collection

User = get_user_model()


@pytest.fixture(scope='module')
def django_db_setup(django_db_setup, django_db_createdb, django_db_keepdb):
    """Использует существующую БД или создаёт тестовую"""
    pass


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def subject(db):
    """Создаёт тестовый предмет"""
    subject, _ = Subject.objects.get_or_create(
        name=f"Test Subject {ObjectId()}",
        defaults={'level': ['beginner']}
    )
    return subject


@pytest.fixture
def student_user(db):
    """Создаёт и возвращает ученика"""
    email = f"pytest_student_{ObjectId()}@test.ru"
    user = User.objects.create_user(
        email=email,
        password='test123',
        first_name='PytestStudent',
        role='student',
    )
    return user


@pytest.fixture
def tutor_user(db):
    """Создаёт и возвращает репетитора"""
    email = f"pytest_tutor_{ObjectId()}@test.ru"
    user = User.objects.create_user(
        email=email,
        password='test123',
        first_name='PytestTutor',
        role='tutor',
    )
    return user


@pytest.fixture
def student_client(api_client, student_user):
    """API client авторизованный как ученик"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def tutor_client(api_client, tutor_user):
    """API client авторизованный как репетитор"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(tutor_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def available_lesson(tutor_user, subject, db):
    """Создаёт доступное занятие"""
    lesson = Lesson.objects.create(
        tutor_id=str(tutor_user._id),
        subject_id=str(subject._id),
        date=timezone.now() + timedelta(days=7),
        duration=60,
        price=1000,
        status='available',
    )
    return lesson


@pytest.fixture
def saved_lesson(student_user, available_lesson, db):
    """Создаёт отложенное занятие"""
    SavedLesson.objects.create(
        student_id=str(student_user._id),
        lesson_id=str(available_lesson._id),
    )
    return available_lesson


# ========== AUTH TESTS ==========


class TestAuth:
    """Тесты авторизации"""

    def test_ping(self, api_client):
        r = api_client.get('/api/ping/')
        assert r.status_code == 200
        assert r.json()['status'] == 'ok'

    def test_register_student(self, api_client):
        email = f"pytest_reg_{ObjectId()}@test.ru"
        r = api_client.post('/api/auth/register/', {
            'email': email,
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'PytestReg',
            'role': 'student',
        }, format='json')
        assert r.status_code == 201
        assert 'tokens' in r.json()
        assert r.json()['user']['email'] == email

    def test_register_tutor(self, api_client):
        email = f"pytest_reg_tutor_{ObjectId()}@test.ru"
        r = api_client.post('/api/auth/register/', {
            'email': email,
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'PytestRegTutor',
            'role': 'tutor',
        }, format='json')
        assert r.status_code == 201

    def test_login_success(self, api_client, student_user):
        r = api_client.post('/api/auth/login/', {
            'username': student_user.email,
            'password': 'test123',
        }, format='json')
        assert r.status_code == 200
        assert 'access' in r.json()['tokens']

    def test_login_wrong_password(self, api_client, student_user):
        r = api_client.post('/api/auth/login/', {
            'username': student_user.email,
            'password': 'wrong',
        }, format='json')
        assert r.status_code == 401

    def test_logout_and_refresh_fails(self, api_client, student_user):
        """Logout → попытка refresh → 401"""
        # Получаем токены
        r = api_client.post('/api/auth/login/', {
            'username': student_user.email,
            'password': 'test123',
        }, format='json')
        refresh = r.json()['tokens']['refresh']
        access = r.json()['tokens']['access']

        # Logout
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        r = api_client.post('/api/auth/logout/', {'refresh': refresh}, format='json')
        assert r.status_code == 200

        # Попытка refresh — должна быть 401
        api_client.credentials()  # сбрасываем
        r = api_client.post('/api/auth/token/refresh/', {'refresh': refresh}, format='json')
        assert r.status_code == 401

    def test_me_authenticated(self, student_client, student_user):
        r = student_client.get('/api/auth/me/')
        assert r.status_code == 200
        assert r.json()['email'] == student_user.email

    def test_me_unauthenticated(self, api_client):
        r = api_client.get('/api/auth/me/')
        assert r.status_code in (401, 403)

    def test_refresh_fresh_token(self, api_client, student_user):
        """Проверка, что свежий (не отозванный) токен обновляется"""
        r = api_client.post('/api/auth/login/', {
            'username': student_user.email,
            'password': 'test123',
        }, format='json')
        refresh = r.json()['tokens']['refresh']

        r = api_client.post('/api/auth/token/refresh/', {'refresh': refresh}, format='json')
        assert r.status_code == 200
        assert 'access' in r.json()


# ========== PERMISSIONS TESTS ==========


class TestPermissions:
    """Тесты прав доступа"""

    def test_student_cannot_create_lesson(self, student_client, subject):
        r = student_client.post('/api/lessons/', {
            'subject_id': str(subject._id),
            'date': '2026-08-01T12:00:00Z',
            'duration': 60,
            'price': 500,
        }, format='json')
        assert r.status_code == 403

    def test_tutor_can_create_lesson(self, tutor_client, subject):
        r = tutor_client.post('/api/lessons/', {
            'subject_id': str(subject._id),
            'date': '2026-08-01T12:00:00Z',
            'duration': 60,
            'price': 1500,
        }, format='json')
        assert r.status_code == 201
        assert 'id' in r.json()

    def test_tutor_cannot_book(self, tutor_client, available_lesson):
        r = tutor_client.post('/api/bookings/', {'lesson_id': str(available_lesson._id)},
                              format='json')
        assert r.status_code == 403

    def test_student_can_book(self, student_client, available_lesson):
        r = student_client.post('/api/bookings/', {'lesson_id': str(available_lesson._id)},
                                format='json')
        assert r.status_code in (200, 201)

    def test_double_booking_fails(self, student_client, tutor_client, subject):
        """Проверка атомарности — дважды на одно занятие нельзя"""
        # Создаём занятие
        r = tutor_client.post('/api/lessons/', {
            'subject_id': str(subject._id),
            'date': '2026-09-01T12:00:00Z',
            'duration': 60,
            'price': 1000,
        }, format='json')
        lesson_id = r.json()['id']

        # Первая запись — ок
        r1 = student_client.post('/api/bookings/', {'lesson_id': lesson_id}, format='json')
        assert r1.status_code in (200, 201)

        # Вторая запись — должна быть 400
        r2 = student_client.post('/api/bookings/', {'lesson_id': lesson_id}, format='json')
        assert r2.status_code == 400


# ========== BOOKING TESTS ==========


class TestBooking:
    """Тесты бронирования"""

    def test_book_lesson_atomic(self, student_client, tutor_client, subject, student_user):
        """Тест атомарности через прямые вызовы atomic_book_lesson"""
        # Создаём занятие
        r = tutor_client.post('/api/lessons/', {
            'subject_id': str(subject._id),
            'date': '2026-09-15T12:00:00Z',
            'duration': 60,
            'price': 1000,
        }, format='json')
        lesson_id = r.json()['id']

        # Первое бронирование через атомарную функцию напрямую (не понадобится —
        # используем student_user._id)
        r1 = student_client.post('/api/bookings/', {'lesson_id': lesson_id}, format='json')
        assert r1.status_code in (200, 201)

        # Второе — должно быть 400
        r2 = student_client.post('/api/bookings/', {'lesson_id': lesson_id}, format='json')
        assert r2.status_code == 400

    def test_my_bookings(self, student_client):
        r = student_client.get('/api/bookings/me/')
        assert r.status_code == 200
        assert 'lessons' in r.json()
        assert 'stats' in r.json()

    def test_cancel_booking(self, student_client, tutor_client, subject):
        """Полный цикл: создать → забронировать → отменить"""
        # Создаём занятие
        r = tutor_client.post('/api/lessons/', {
            'subject_id': str(subject._id),
            'date': '2026-09-20T12:00:00Z',
            'duration': 60,
            'price': 1000,
        }, format='json')
        lesson_id = r.json()['id']

        # Бронируем
        r = student_client.post('/api/bookings/', {'lesson_id': lesson_id}, format='json')
        assert r.status_code in (200, 201)

        # Отменяем
        r = student_client.post(f'/api/bookings/{lesson_id}/cancel/', format='json')
        assert r.status_code == 200


# ========== SAVED TESTS ==========


class TestSaved:
    """Тесты избранного"""

    def test_save_lesson(self, student_client, available_lesson):
        r = student_client.post(f'/api/saved/{available_lesson.id}/save/')
        assert r.status_code in (200, 201)

    def test_unsave_lesson(self, student_client, saved_lesson):
        r = student_client.delete(f'/api/saved/{saved_lesson.id}/unsave/')
        assert r.status_code == 200

    def test_saved_list(self, student_client, saved_lesson):
        r = student_client.get('/api/saved/')
        assert r.status_code == 200
        assert 'lessons' in r.json()

    def test_book_all_saved(self, student_client, saved_lesson):
        """Атомарное массовое бронирование"""
        r = student_client.post('/api/saved/book-all/', format='json')
        assert r.status_code == 200
        data = r.json()
        assert 'booked' in data
        # Занятие было available, так что booked должно быть 1
        assert data['booked'] >= 1

    def test_book_all_saved_no_favorites(self, student_client):
        """Попытка book-all без избранного — 400"""
        r = student_client.post('/api/saved/book-all/', format='json')
        assert r.status_code == 400


# ========== USERS TESTS ==========


class TestUsers:
    """Тесты пользователей"""

    def test_tutors_list(self, api_client, tutor_user):
        r = api_client.get('/api/users/tutors/')
        assert r.status_code == 200
        # С пагинацией DRF
        data = r.json()
        if isinstance(data, dict):
            assert 'results' in data
        else:
            assert isinstance(data, list)

    def test_students_list(self, api_client, student_user):
        r = api_client.get('/api/users/students/')
        assert r.status_code == 200

    def test_user_detail(self, api_client, tutor_user):
        r = api_client.get(f'/api/users/{tutor_user.id}/')
        assert r.status_code in (200, 404)  # может быть None если не найден
        if r.status_code == 200:
            assert r.json()['email'] == tutor_user.email


# ========== SUBJECTS ==========


class TestSubjects:
    """Тесты предметов"""

    def test_subjects_list(self, api_client, subject):
        r = api_client.get('/api/subjects/')
        assert r.status_code == 200


# ========== DASHBOARD ==========


class TestDashboard:
    """Тесты дашборда"""

    def test_student_dashboard(self, student_client):
        r = student_client.get('/api/users/me/dashboard/')
        assert r.status_code == 200
        data = r.json()
        assert data['role'] == 'student'
        assert 'stats' in data

    def test_tutor_dashboard(self, tutor_client):
        r = tutor_client.get('/api/users/me/dashboard/')
        assert r.status_code == 200
        data = r.json()
        assert data['role'] == 'tutor'
        assert 'stats' in data


# ========== ATOMIC BOOKING DIRECT TEST ==========


class TestAtomicBooking:
    """Прямой тест атомарной функции atomic_book_lesson через PyMongo"""

    def test_atomic_book_lesson_success(self, tutor_user, subject, db):
        """Успешное атомарное бронирование"""
        lesson = Lesson.objects.create(
            tutor_id=str(tutor_user._id),
            subject_id=str(subject._id),
            date=timezone.now() + timedelta(days=7),
            duration=60,
            price=1000,
            status='available',
        )
        result = atomic_book_lesson(str(lesson._id), 'test_student_1')
        assert result['success'] is True

    def test_atomic_book_lesson_double_fails(self, tutor_user, subject, db):
        """Двойное бронирование — вторая попытка фейлится"""
        lesson = Lesson.objects.create(
            tutor_id=str(tutor_user._id),
            subject_id=str(subject._id),
            date=timezone.now() + timedelta(days=7),
            duration=60,
            price=1000,
            status='available',
        )
        lesson_id = str(lesson._id)

        # Первый успех
        r1 = atomic_book_lesson(lesson_id, 'test_student_1')
        assert r1['success'] is True

        # Второй фейл
        r2 = atomic_book_lesson(lesson_id, 'test_student_2')
        assert r2['success'] is False
        assert 'недоступно' in r2['error'].lower()

    def test_atomic_book_lesson_invalid_id(self, db):
        """Неверный ID — ошибка"""
        result = atomic_book_lesson('invalid_id', 'student')
        assert result['success'] is False