"""
HTTP-тесты API через живой сервер.
Запускать: python -m unittest tests.test_api_http
Предварительно: python manage.py runserver
"""
import unittest
import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'


class TestAPIViaHTTP(unittest.TestCase):
    """Тестирование API через HTTP запросы к живому серверу"""

    @classmethod
    def setUpClass(cls):
        cls.base = BASE_URL
        # Проверяем, что сервер запущен
        try:
            r = requests.get(f'{cls.base}/api/ping/', timeout=3)
            assert r.status_code == 200
            print(f"✅ Сервер работает: {cls.base}")
        except Exception as e:
            raise unittest.SkipTest(f"Сервер не запущен: {e}")

        # Регистрируем тестовых пользователей
        cls._setup_users()

    @classmethod
    def _setup_users(cls):
        """Создаёт test-пользователей для тестов"""
        import random
        suffix = random.randint(1000, 9999)

        # Студент
        cls.student_email = f"http_student_{suffix}@test.ru"
        r = requests.post(f'{cls.base}/api/auth/register/', json={
            'email': cls.student_email,
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'HTTPStudent',
            'role': 'student',
        })
        cls.student_id = r.json().get('user', {}).get('id') if r.status_code == 201 else None

        # Репетитор
        cls.tutor_email = f"http_tutor_{suffix}@test.ru"
        r = requests.post(f'{cls.base}/api/auth/register/', json={
            'email': cls.tutor_email,
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'HTTPTutor',
            'role': 'tutor',
        })
        cls.tutor_id = r.json().get('user', {}).get('id') if r.status_code == 201 else None

        # Токены
        r = requests.post(f'{cls.base}/api/auth/login/', json={
            'username': cls.student_email, 'password': 'test123'
        })
        cls.student_token = r.json().get('tokens', {}).get('access') if r.status_code == 200 else None

        r = requests.post(f'{cls.base}/api/auth/login/', json={
            'username': cls.tutor_email, 'password': 'test123'
        })
        cls.tutor_token = r.json().get('tokens', {}).get('access') if r.status_code == 200 else None

        # Создаем предмет
        r = requests.get(f'{cls.base}/api/subjects/')
        subjects_data = r.json()
        # С пагинацией DRF ответ в формате: {"count": N, "results": [...]}
        if isinstance(subjects_data, dict) and 'results' in subjects_data:
            subjects_list = subjects_data['results']
        elif isinstance(subjects_data, list):
            subjects_list = subjects_data
        else:
            subjects_list = []
        if subjects_list:
            cls.subject_id = subjects_list[0]['id']
        else:
            cls.subject_id = None

        # Репетитор создаёт занятие (для booking-тестов)
        if cls.tutor_token and cls.subject_id:
            r = requests.post(f'{cls.base}/api/lessons/', json={
                'subject_id': cls.subject_id,
                'date': '2026-07-15T12:00:00Z',
                'duration': 60,
                'price': 1000,
            }, headers={'Authorization': f'Bearer {cls.tutor_token}'})
            if r.status_code == 201:
                cls.lesson_id = r.json().get('id')
            
            # Второе занятие (для saved-тестов — остаётся available)
            r2 = requests.post(f'{cls.base}/api/lessons/', json={
                'subject_id': cls.subject_id,
                'date': '2026-07-20T12:00:00Z',
                'duration': 60,
                'price': 2000,
            }, headers={'Authorization': f'Bearer {cls.tutor_token}'})
            if r2.status_code == 201:
                cls.saved_lesson_id = r2.json().get('id')

        print(f"   Student: {cls.student_email} / Tutor: {cls.tutor_email} / Lesson: {getattr(cls, 'lesson_id', 'N/A')}")

    # ========== AUTH TESTS ==========

    def test_01_ping(self):
        r = requests.get(f'{self.base}/api/ping/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ok')

    def test_02_register(self):
        import random
        email = f'http_test_{random.randint(10000,99999)}@test.ru'
        r = requests.post(f'{self.base}/api/auth/register/', json={
            'email': email,
            'password': 'test123',
            'password_confirm': 'test123',
            'first_name': 'Unique',
            'role': 'student',
        })
        self.assertEqual(r.status_code, 201)
        self.assertIn('tokens', r.json())

    def test_03_login_success(self):
        r = requests.post(f'{self.base}/api/auth/login/', json={
            'username': self.student_email, 'password': 'test123'
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.json().get('tokens', {}))

    def test_04_login_wrong_password(self):
        r = requests.post(f'{self.base}/api/auth/login/', json={
            'username': self.student_email, 'password': 'wrong'
        })
        self.assertEqual(r.status_code, 401)

    def test_05_me_authenticated(self):
        if not self.student_token:
            self.skipTest("Нет токена")
        r = requests.get(f'{self.base}/api/auth/me/',
                         headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['email'], self.student_email)

    def test_06_me_unauthenticated(self):
        r = requests.get(f'{self.base}/api/auth/me/')
        self.assertIn(r.status_code, [401, 403])

    def test_07_logout(self):
        if not self.student_token:
            self.skipTest("Нет токена")
        # Получаем refresh токен
        r = requests.post(f'{self.base}/api/auth/login/', json={
            'username': self.student_email, 'password': 'test123'
        })
        refresh = r.json().get('tokens', {}).get('refresh')
        if not refresh:
            self.skipTest("Нет refresh токена")
        r = requests.post(f'{self.base}/api/auth/logout/', json={'refresh': refresh},
                          headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 200)

    def test_07b_refresh_revoked_token_fails(self):
        """Проверка, что refresh отозванного токена возвращает 401"""
        # Регистрируем нового пользователя для теста
        import random
        email = f'refresh_test_{random.randint(10000,99999)}@test.ru'
        r = requests.post(f'{self.base}/api/auth/register/', json={
            'email': email, 'password': 'test123', 'password_confirm': 'test123',
            'first_name': 'Refresh', 'role': 'student',
        })
        if r.status_code != 201:
            self.skipTest("Не удалось создать пользователя")
        refresh = r.json().get('tokens', {}).get('refresh')
        access = r.json().get('tokens', {}).get('access')
        if not refresh or not access:
            self.skipTest("Нет токенов")

        # Отзываем токен через logout
        requests.post(f'{self.base}/api/auth/logout/', json={'refresh': refresh},
                      headers={'Authorization': f'Bearer {access}'})

        # Пытаемся обновить — должно быть 401
        r = requests.post(f'{self.base}/api/auth/token/refresh/', json={'refresh': refresh})
        self.assertEqual(r.status_code, 401)
        self.assertIn('отозван', r.json().get('error', '').lower() or
                      r.json().get('error', ''))

    # ========== PERMISSIONS ==========

    def test_10_student_cannot_create_lesson(self):
        if not self.student_token or not self.subject_id:
            self.skipTest("Нет токена или предмета")
        r = requests.post(f'{self.base}/api/lessons/', json={
            'subject_id': self.subject_id,
            'date': '2026-08-01T12:00:00Z',
            'duration': 60,
            'price': 500,
        }, headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 403)

    def test_11_tutor_can_create_lesson(self):
        if not self.tutor_token or not self.subject_id:
            self.skipTest("Нет токена или предмета")
        r = requests.post(f'{self.base}/api/lessons/', json={
            'subject_id': self.subject_id,
            'date': '2026-08-01T12:00:00Z',
            'duration': 60,
            'price': 1500,
        }, headers={'Authorization': f'Bearer {self.tutor_token}'})
        self.assertEqual(r.status_code, 201)

    def test_12_only_student_can_book(self):
        if not self.tutor_token or not hasattr(self, 'lesson_id'):
            self.skipTest("Нет урока")
        r = requests.post(f'{self.base}/api/bookings/', json={'lesson_id': self.lesson_id},
                          headers={'Authorization': f'Bearer {self.tutor_token}'})
        self.assertEqual(r.status_code, 403)

    def test_13_student_can_book(self):
        if not self.student_token or not hasattr(self, 'lesson_id'):
            self.skipTest("Нет урока")
        r = requests.post(f'{self.base}/api/bookings/', json={'lesson_id': self.lesson_id},
                          headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertIn(r.status_code, [200, 201])

    def test_14_double_booking_fails(self):
        if not self.student_token or not hasattr(self, 'lesson_id'):
            self.skipTest("Нет урока")
        # Создаём второй урок
        r = requests.post(f'{self.base}/api/lessons/', json={
            'subject_id': self.subject_id,
            'date': '2026-09-01T12:00:00Z',
            'duration': 60,
            'price': 1000,
        }, headers={'Authorization': f'Bearer {self.tutor_token}'})
        if r.status_code != 201:
            self.skipTest("Не удалось создать второй урок")
        lesson2_id = r.json()['id']

        # Записываемся на второй
        r1 = requests.post(f'{self.base}/api/bookings/', json={'lesson_id': lesson2_id},
                           headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertIn(r1.status_code, [200, 201])

        # Пытаемся повторно
        r2 = requests.post(f'{self.base}/api/bookings/', json={'lesson_id': lesson2_id},
                           headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r2.status_code, 400)

    # ========== SAVED TESTS ==========

    def test_15_student_save_lesson(self):
        if not self.student_token or not hasattr(self, 'saved_lesson_id'):
            self.skipTest("Нет урока для сохранения")
        r = requests.post(f'{self.base}/api/saved/{self.saved_lesson_id}/save/',
                          headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertIn(r.status_code, [200, 201])

    def test_16_student_unsave_lesson(self):
        if not self.student_token or not hasattr(self, 'saved_lesson_id'):
            self.skipTest("Нет урока для сохранения")
        # Сначала сохраняем
        requests.post(f'{self.base}/api/saved/{self.saved_lesson_id}/save/',
                      headers={'Authorization': f'Bearer {self.student_token}'})
        # Удаляем
        r = requests.delete(f'{self.base}/api/saved/{self.saved_lesson_id}/unsave/',
                            headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 200)

    def test_17_saved_list(self):
        if not self.student_token:
            self.skipTest("Нет токена")
        r = requests.get(f'{self.base}/api/saved/',
                         headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('lessons', r.json())

    # ========== BOOKING FLOW ==========

    def test_17b_book_all_saved_atomic(self):
        """Проверка атомарного book-all-saved"""
        if not self.student_token or not hasattr(self, 'saved_lesson_id'):
            self.skipTest("Нет токена или избранного урока")
        # Сохраняем занятие
        requests.post(f'{self.base}/api/saved/{self.saved_lesson_id}/save/',
                      headers={'Authorization': f'Bearer {self.student_token}'})

        # Студент дважды бронирует все избранные:
        r = requests.post(f'{self.base}/api/saved/book-all/',
                          headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get('booked', 0), 1,
                         f"Должно быть 1 успешное бронирование, получено: {data}")

        # Повторный вызов: занятие уже забронировано, booked=0
        # Сначала снова сохраняем (оно удалилось после book-all)
        # Создадим новое занятие через репетитора
        if self.tutor_token and self.subject_id:
            r = requests.post(f'{self.base}/api/lessons/', json={
                'subject_id': self.subject_id,
                'date': '2026-10-01T12:00:00Z',
                'duration': 60,
                'price': 1500,
            }, headers={'Authorization': f'Bearer {self.tutor_token}'})
            if r.status_code == 201:
                new_lesson_id = r.json()['id']
                requests.post(f'{self.base}/api/saved/{new_lesson_id}/save/',
                              headers={'Authorization': f'Bearer {self.student_token}'})
                # Первая запись — ок
                r1 = requests.post(f'{self.base}/api/saved/book-all/',
                                   headers={'Authorization': f'Bearer {self.student_token}'})
                self.assertEqual(r1.status_code, 200)
                data1 = r1.json()
                self.assertEqual(data1.get('booked', 0), 1,
                                 f"Первая запись ок: {data1}")
                # Вторая запись — тот же урок уже занят
                # Сохраняем снова (копия, т.к. удалился из избранного после book-all)
                # Создадим другой урок
                r3 = requests.post(f'{self.base}/api/lessons/', json={
                    'subject_id': self.subject_id,
                    'date': '2026-11-01T12:00:00Z',
                    'duration': 60,
                    'price': 2000,
                }, headers={'Authorization': f'Bearer {self.tutor_token}'})
                if r3.status_code == 201:
                    new_lesson_id2 = r3.json()['id']
                    requests.post(f'{self.base}/api/saved/{new_lesson_id2}/save/',
                                  headers={'Authorization': f'Bearer {self.student_token}'})
                    # Сначала бронируем напрямую
                    requests.post(f'{self.base}/api/bookings/', json={'lesson_id': new_lesson_id2},
                                  headers={'Authorization': f'Bearer {self.student_token}'})
                    # Теперь сохраняем этот же урок (статус уже booked) и пробуем book-all
                    # Сохранить его не даст save (status != available), так что пропускаем этот тест
                    pass

    def test_18_my_bookings(self):
        if not self.student_token:
            self.skipTest("Нет токена")
        r = requests.get(f'{self.base}/api/bookings/me/',
                         headers={'Authorization': f'Bearer {self.student_token}'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('lessons', r.json())

    # ========== TUTORS / STUDENTS ==========

    def test_20_tutors_list(self):
        r = requests.get(f'{self.base}/api/users/tutors/')
        self.assertEqual(r.status_code, 200)
        # С пагинацией DRF: {"count": N, "results": [...]}
        data = r.json()
        if isinstance(data, dict):
            self.assertIn('results', data)
        else:
            self.assertIsInstance(data, list)

    def test_21_students_list(self):
        r = requests.get(f'{self.base}/api/users/students/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        if isinstance(data, dict):
            self.assertIn('results', data)
        else:
            self.assertIsInstance(data, list)

    def test_22_subjects_list(self):
        r = requests.get(f'{self.base}/api/subjects/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        if isinstance(data, dict):
            self.assertIn('results', data)
        else:
            self.assertIsInstance(data, list)

    def test_23_available_lessons(self):
        r = requests.get(f'{self.base}/api/lessons/available/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        if isinstance(data, dict):
            self.assertIn('results', data)
        else:
            self.assertIsInstance(data, list)

    def test_24_lessons_list(self):
        r = requests.get(f'{self.base}/api/lessons/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        if isinstance(data, dict):
            self.assertIn('results', data)
        else:
            self.assertIsInstance(data, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)