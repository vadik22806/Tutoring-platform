# StudyEasy — Tutoring Platform

Краткая документация для запуска и использования.

## Что это

StudyEasy — Django-платформа для поиска репетиторов и записи на занятия.
Проект сочетает:
- Django + MongoDB (`djongo`)
- REST API на Django REST Framework
- JWT-авторизацию
- старый пользовательский интерфейс на Django Templates

## Что важно

- Корневая команда запуска: `python manage.py` из корня проекта
- Основной файл настроек: `echoserver/config/settings.py`
- Проект использует MongoDB через `djongo`
- Сервис API доступен по префиксу `/api/`
- `echoserver/.env.example` хранит пример переменных окружения

## Система и зависимости

- Python 3.11
- Django 3.1.12
- djangorestframework 3.12.4
- djangorestframework-simplejwt 4.8.0
- djongo 1.3.7
- pymongo 3.11.4
- pytest 7.4

## Быстрая установка

```bash
cd /path/to/Web_development
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp echoserver/.env.example echoserver/.env
```

Отредактируйте `echoserver/.env`, если необходимо.

## Запуск

```bash
python manage.py migrate
python manage.py runserver
```

После запуска:
- Веб: http://127.0.0.1:8000/
- API test: http://127.0.0.1:8000/api/ping/

## MongoDB

В `echoserver/config/settings.py` указано:
- host: `mongodb://localhost:27017`
- database: `Tutoring`

Перед запуском убедитесь, что MongoDB работает локально.

## Основные API маршруты

Все API маршруты начинаются с `/api/`.

### Авторизация
- `POST /api/auth/register/` — регистрация
- `POST /api/auth/login/` — логин
- `POST /api/auth/logout/` — выход
- `POST /api/auth/token/refresh/` — обновление токена
- `GET /api/auth/me/` — профиль текущего пользователя

### Пользователи
- `GET /api/users/tutors/` — список репетиторов
- `GET /api/users/students/` — список студентов
- `GET /api/users/<id>/` — пользователь
- `POST /api/users/<id>/update/` — обновление пользователя
- `GET /api/users/me/dashboard/` — личный дашборд

### Занятия
- `GET /api/lessons/available/` — доступные занятия
- `GET, POST /api/lessons/` — список / создание
- `GET, PUT, DELETE /api/lessons/<id>/` — управление занятием
- `POST /api/lessons/<id>/complete/` — завершить
- `POST /api/lessons/<id>/cancel/` — отменить

### Записи и избранное
- `POST /api/bookings/` — запись на занятие
- `POST /api/bookings/<id>/cancel/` — отмена записи
- `GET /api/bookings/me/` — мои записи
- `GET /api/saved/` — избранные занятия
- `POST /api/saved/<id>/save/` — добавить в избранное
- `POST /api/saved/<id>/unsave/` — убрать из избранного
- `POST /api/saved/book-all/` — записаться на всё избранное

### Предметы и проверки
- `GET /api/subjects/` — список предметов
- `GET /api/check-email/` — проверка email
- `GET /api/check-phone/` — проверка телефона

## Тестирование

```bash
python -m pytest tests/test_api_pytest.py -v
```

## Примечания

- В проекте используется пользовательская модель `main.User`.
- Админка доступна по `/admin/`.
- Если нужно восстановить настройки, смотрите `echoserver/config/settings.py`.
