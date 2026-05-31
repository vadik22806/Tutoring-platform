# PROGRESS — Рефакторинг StudyEasy

## Сделано

- 31.05.2026 — Добавлен файл `echoserver/TECHNICAL_SPEC_AI_AGENT.md` с техническим заданием для ИИ-агента.
- 31.05.2026 — Добавлен `echoserver/TECHNICAL_SPEC_AI_AGENT.md` в `.gitignore`.
- 31.05.2026 — Локальный Django dev-сервер запущен: http://127.0.0.1:8000/.
- 31.05.2026 — Создано приложение `api` и добавлены заготовки `serializers.py`, `views.py`, `urls.py`.
- 31.05.2026 — Установлены зависимости: `djangorestframework`, `djangorestframework-simplejwt`.
 - 31.05.2026 — Проверены эндпоинты: `/api/ping/` (OK), `/api/subjects/` (вернул список предметов).
 - 31.05.2026 — Временно убрана жёсткая сортировка по `first_name` для `tutors`/`students` (fallback при ошибке БД), чтобы страница `tutors` работала при несовместимости `djongo`.
- 31.05.2026 — Сохранено текущее окружение в `before_pin_requirements.txt` и создан `requirements.txt` с зафиксированными версиями пакетов.
- 31.05.2026 — Восстановлено рабочее состояние окружения `.venv` для текущих зависимостей и проверено `python echoserver/manage.py check`.
- 31.05.2026 — Создан файл `echoserver/ENVIRONMENT_ISSUE_AND_FIX.md` с описанием проблемы совместимости Python 3.12, `setuptools`, `djongo` и `simplejwt`.
- 31.05.2026 — Установлен Python 3.11.15 через Homebrew и пересоздано виртуальное окружение `.venv` с Python 3.11.
- 31.05.2026 — Проверена работа Django и API на Python 3.11: `/api/ping/` и `/api/subjects/` возвращают 200 OK.
- 31.05.2026 — Подтверждено: текущий стек полностью совместим с Python 3.11, проблема с `pkg_resources` устранена переходом на Python 3.11.

## Следующие шаги

- Создать приложение `api` и scaffold (serializers, urls, views).
- Установить `djangorestframework` и `djangorestframework-simplejwt`.
- Написать сериализаторы для моделей и реализовать MVP-эндпоинты.
