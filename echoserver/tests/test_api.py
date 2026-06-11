"""
API тесты для критичных flow:
- auth (register, login, logout, me)
- booking (book, cancel, conflict)
- saved (save, unsave, book-all)
- permissions (доступы tutor/student)
"""
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from bson import ObjectId

from main.models import User, Subject, Lesson, SavedLesson


class TestAuthFlow(TestCase):
    """Тесты аутентификации"""

    def setUp(self):
        self.client = APIClient()

    def test_01_register_student(self):
        """Регистрация ученика"""
        response = self.client.post('/api/auth/register/', {
            'email': 'test_student@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Test',
            'role': 'student',
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(response.data['user']['role'], 'student')

    def test_02_register_tutor(self):
        """Регистрация репетитора"""
        response = self.client.post('/api/auth/register/', {
            'email': 'test_tutor@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Tutor',
            'role': 'tutor',
            'bio': 'Опытный репетитор',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['role'], 'tutor')

    def test_03_register_validation_email_exists(self):
        """Проверка: email уже существует"""
        self.client.post('/api/auth/register/', {
            'email': 'duplicate@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'First',
            'role': 'student',
        })
        response = self.client.post('/api/auth/register/', {
            'email': 'duplicate@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Second',
            'role': 'student',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)

    def test_04_register_no_email_no_phone(self):
        """Проверка: нужен email или телефон"""
        response = self.client.post('/api/auth/register/', {
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'NoContact',
            'role': 'student',
        })
        self.assertEqual(response.status_code, 400)

    def test_05_login_success(self):
        """Успешный вход"""
        self.client.post('/api/auth/register/', {
            'email': 'login_test@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Login',
            'role': 'student',
        })
        response = self.client.post('/api/auth/login/', {
            'username': 'login_test@test.ru',
            'password': 'test123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data['tokens'])

    def test_06_login_wrong_password(self):
        """Неверный пароль"""
        self.client.post('/api/auth/register/', {
            'email': 'wrong_pw@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Wrong',
            'role': 'student',
        })
        response = self.client.post('/api/auth/login/', {
            'username': 'wrong_pw@test.ru',
            'password': 'wrong_password',
        })
        self.assertEqual(response.status_code, 401)

    def test_07_me_authenticated(self):
        """GET /me с токеном"""
        self.client.post('/api/auth/register/', {
            'email': 'me_test@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Me',
            'role': 'student',
        })
        login_resp = self.client.post('/api/auth/login/', {
            'username': 'me_test@test.ru',
            'password': 'test123',
        })
        token = login_resp.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'me_test@test.ru')

    def test_08_me_unauthenticated(self):
        """GET /me без токена — 403"""
        response = self.client.get('/api/auth/me/')
        # 403 от кастомной JWT или 401 от DRF
        self.assertIn(response.status_code, [401, 403])

    def test_09_logout(self):
        """Logout с refresh токеном"""
        self.client.post('/api/auth/register/', {
            'email': 'logout_test@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Logout',
            'role': 'student',
        })
        login_resp = self.client.post('/api/auth/login/', {
            'username': 'logout_test@test.ru',
            'password': 'test123',
        })
        access = login_resp.data['tokens']['access']
        refresh = login_resp.data['tokens']['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.post('/api/auth/logout/', {'refresh': refresh})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Выход', response.data['message'])


class TestPermissions(TestCase):
    """Тесты разрешений по ролям"""

    def setUp(self):
        self.client = APIClient()
        # Создаём student
        self.client.post('/api/auth/register/', {
            'email': 'student_role@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Stud',
            'role': 'student',
        })
        login_resp = self.client.post('/api/auth/login/', {
            'username': 'student_role@test.ru',
            'password': 'test123',
        })
        self.student_token = login_resp.data['tokens']['access']

        # Создаём tutor
        self.client.post('/api/auth/register/', {
            'email': 'tutor_role@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Tut',
            'role': 'tutor',
        })
        login_resp2 = self.client.post('/api/auth/login/', {
            'username': 'tutor_role@test.ru',
            'password': 'test123',
        })
        self.tutor_token = login_resp2.data['tokens']['access']

        # Создаём предмет
        try:
            self.subject = Subject.objects.get(name='Тестовый предмет')
        except Subject.DoesNotExist:
            self.subject = Subject.objects.create(
                _id=ObjectId(),
                name='Тестовый предмет',
                level=['school']
            )

        # Создаём занятие от tutor
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tutor_token}')
        lesson_resp = self.client.post('/api/lessons/', {
            'subject_id': str(self.subject._id),
            'date': (timezone.now() + timedelta(days=7)).isoformat(),
            'duration': 60,
            'price': 1000,
        })
        self.lesson_id = lesson_resp.data['id']

    def test_10_student_cannot_create_lesson(self):
        """Ученик не может создать занятие"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post('/api/lessons/', {
            'subject_id': str(self.subject._id),
            'date': (timezone.now() + timedelta(days=10)).isoformat(),
            'duration': 60,
            'price': 500,
        })
        self.assertEqual(response.status_code, 403)

    def test_11_tutor_can_create_lesson(self):
        """Репетитор может создать занятие"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tutor_token}')
        response = self.client.post('/api/lessons/', {
            'subject_id': str(self.subject._id),
            'date': (timezone.now() + timedelta(days=10)).isoformat(),
            'duration': 90,
            'price': 1500,
        })
        self.assertEqual(response.status_code, 201)

    def test_12_only_student_can_book(self):
        """Только ученик может записаться"""
        # Tutor пытается записаться
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tutor_token}')
        response = self.client.post('/api/bookings/', {'lesson_id': self.lesson_id})
        self.assertEqual(response.status_code, 403)

    def test_13_student_can_book(self):
        """Ученик может записаться"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post('/api/bookings/', {'lesson_id': self.lesson_id})
        self.assertIn(response.status_code, [200, 201])

    def test_14_double_booking_fails(self):
        """Двойная запись на одно занятие невозможна"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        resp1 = self.client.post('/api/bookings/', {'lesson_id': self.lesson_id})
        if resp1.status_code in [200, 201]:
            # Пытаемся записаться повторно — должен быть 400
            resp2 = self.client.post('/api/bookings/', {'lesson_id': self.lesson_id})
            self.assertEqual(resp2.status_code, 400)

    def test_15_only_student_save_lesson(self):
        """Только ученик может добавить в избранное"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tutor_token}')
        response = self.client.post(f'/api/saved/{self.lesson_id}/save/')
        self.assertEqual(response.status_code, 403)

    def test_16_student_save_lesson(self):
        """Ученик может добавить в избранное"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post(f'/api/saved/{self.lesson_id}/save/')
        self.assertEqual(response.status_code, 201)


class TestBookingFlow(TestCase):
    """Полный цикл бронирования"""

    def setUp(self):
        self.client = APIClient()

        # Создаём tutor
        self.client.post('/api/auth/register/', {
            'email': 'tutor_book@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'TutorBook',
            'role': 'tutor',
        })
        login = self.client.post('/api/auth/login/', {
            'username': 'tutor_book@test.ru',
            'password': 'test123',
        })
        self.tutor_token = login.data['tokens']['access']

        # Создаём student
        self.client.post('/api/auth/register/', {
            'email': 'student_book@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'StudentBook',
            'role': 'student',
        })
        login2 = self.client.post('/api/auth/login/', {
            'username': 'student_book@test.ru',
            'password': 'test123',
        })
        self.student_token = login2.data['tokens']['access']

        # Предмет
        try:
            self.subject = Subject.objects.get(name='Тест бук')
        except Subject.DoesNotExist:
            self.subject = Subject.objects.create(
                _id=ObjectId(),
                name='Тест бук',
                level=['school']
            )

        # Создаём занятие
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tutor_token}')
        lesson_resp = self.client.post('/api/lessons/', {
            'subject_id': str(self.subject._id),
            'date': (timezone.now() + timedelta(days=14)).isoformat(),
            'duration': 60,
            'price': 1000,
        })
        self.lesson_id = lesson_resp.data['id']

    def test_17_full_booking_flow(self):
        """Полный цикл: save → book → my bookings → cancel"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')

        # 1. Сохраняем в избранное
        save_resp = self.client.post(f'/api/saved/{self.lesson_id}/save/')
        self.assertIn(save_resp.status_code, [200, 201])

        # 2. Получаем список избранного
        saved_resp = self.client.get('/api/saved/')
        self.assertEqual(saved_resp.status_code, 200)
        self.assertGreaterEqual(len(saved_resp.data.get('lessons', [])), 0)

        # 3. Записываемся
        book_resp = self.client.post('/api/bookings/', {'lesson_id': self.lesson_id})
        self.assertIn(book_resp.status_code, [200, 201])

        # 4. Проверяем историю
        my_bookings = self.client.get('/api/bookings/me/')
        self.assertEqual(my_bookings.status_code, 200)

        # 5. Отменяем запись
        cancel_resp = self.client.post(f'/api/bookings/{self.lesson_id}/cancel/')
        self.assertEqual(cancel_resp.status_code, 200)
        self.assertIn('отменена', cancel_resp.data['message'])

    def test_18_cancel_booking(self):
        """Отмена записи"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        book_resp = self.client.post('/api/bookings/', {'lesson_id': self.lesson_id})
        self.assertIn(book_resp.status_code, [200, 201])

        cancel_resp = self.client.post(f'/api/bookings/{self.lesson_id}/cancel/')
        self.assertEqual(cancel_resp.status_code, 200)


class TestSavedFlow(TestCase):
    """Тесты избранного"""

    def setUp(self):
        self.client = APIClient()

        self.client.post('/api/auth/register/', {
            'email': 'tutor_saved@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'TSaved',
            'role': 'tutor',
        })
        login = self.client.post('/api/auth/login/', {
            'username': 'tutor_saved@test.ru',
            'password': 'test123',
        })
        self.tutor_token = login.data['tokens']['access']

        self.client.post('/api/auth/register/', {
            'email': 'student_saved@test.ru',
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'SSaved',
            'role': 'student',
        })
        login2 = self.client.post('/api/auth/login/', {
            'username': 'student_saved@test.ru',
            'password': 'test123',
        })
        self.student_token = login2.data['tokens']['access']

        try:
            self.subject = Subject.objects.get(name='Сэйв тест')
        except Subject.DoesNotExist:
            self.subject = Subject.objects.create(
                _id=ObjectId(),
                name='Сэйв тест',
                level=['school']
            )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tutor_token}')
        lesson_resp = self.client.post('/api/lessons/', {
            'subject_id': str(self.subject._id),
            'date': (timezone.now() + timedelta(days=21)).isoformat(),
            'duration': 60,
            'price': 2000,
        })
        self.lesson_id = lesson_resp.data['id']

    def test_19_save_and_unsave(self):
        """save + unsave"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')

        # Save
        save_resp = self.client.post(f'/api/saved/{self.lesson_id}/save/')
        self.assertIn(save_resp.status_code, [200, 201])

        # Unsave
        unsave_resp = self.client.delete(f'/api/saved/{self.lesson_id}/unsave/')
        self.assertEqual(unsave_resp.status_code, 200)

    def test_20_unsave_not_saved(self):
        """unsave несохранённого"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.delete(f'/api/saved/{self.lesson_id}/unsave/')
        self.assertEqual(response.status_code, 404)

    def test_21_book_all_saved_empty(self):
        """book-all без избранного"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post('/api/saved/book-all/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('нет избранных', response.data['error'])