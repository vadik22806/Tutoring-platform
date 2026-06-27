# StudyEasy — Tutoring Platform

Платформа для поиска репетиторов и записи на занятия. Django + MongoDB + REST API.

## Стек

- **Python 3.11**, Django 3.1.12, DRF 3.12.4
- **MongoDB** (djongo + PyMongo)
- **JWT** авторизация (djangorestframework-simplejwt)
- **pytest** (31 тест)

## Структура

```
echoserver/
├── config/            # Настройки Django (DRF, JWT, БД)
├── main/              # Старый сайт (шаблоны, сессии)
├── api/               # REST API (27 эндпоинтов)
│   ├── views.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── authentication.py
│   └── utils.py       # Атомарные операции с MongoDB
├── tests/             # pytest-тесты
├── manage.py
├── .env.example       # Шаблон настроек (скопировать в .env)
└── requirements.txt
```

## Быстрый старт

```bash
# 1. Виртуальное окружение
python3 -m venv .venv && source .venv/bin/activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Настройки
cp echoserver/.env.example echoserver/.env
# Отредактировать echoserver/.env при необходимости

# 4. MongoDB (должен быть запущен локально)

# 5. Запуск
cd echoserver && python manage.py runserver
```

Сайт: http://127.0.0.1:8000/
API: http://127.0.0.1:8000/api/ping/

## Тесты

```bash
cd echoserver && python -m pytest tests/test_api_pytest.py -v
```

## API Эндпоинты

| Категория | Эндпоинты |
|-----------|-----------|
| Auth | register, login, logout, token/refresh, me |
| Users | tutors, students, profile, update, dashboard |
| Lessons | list, create, detail, update, delete, complete, cancel |
| Bookings | book, cancel, my-bookings |
| Saved | list, save, unsave, book-all |
| Subjects | list |
| Ajax | check-email, check-phone |

Полная документация: `echoserver/TECHNICAL_SPEC_AND_API_DOCS.md`