"""
API утилиты: атомарные операции с БД, логирование и др.
"""
import logging
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId

logger = logging.getLogger(__name__)


def get_mongo_collection(collection_name):
    """
    Возвращает PyMongo коллекцию для прямых атомарных операций,
    в обход djongo ORM.
    """
    db_config = settings.DATABASES['default']
    client = MongoClient(
        host=db_config['CLIENT']['host'],
    )
    db = client[db_config['NAME']]
    return db[collection_name]


def atomic_book_lesson(lesson_id, student_id):
    """
    Атомарная запись ученика на занятие.

    Использует MongoDB find_one_and_update с фильтром:
      - _id == lesson_id
      - status == 'available'
      - date > now (не прошедшее)

    Возвращает dict с результатом:
      - success: True/False
      - error: сообщение об ошибке (если не успешно)
      - lesson: данные занятия (если успешно)
    """
    from django.utils import timezone

    lessons_collection = get_mongo_collection('lessons')
    now = timezone.now()

    try:
        lesson_id_obj = ObjectId(lesson_id)
    except Exception as e:
        logger.error(f"Invalid lesson_id format: {lesson_id} - {e}")
        return {'success': False, 'error': 'Неверный формат ID занятия'}

    # Атомарное обновление: найти и обновить за одну операцию
    result = lessons_collection.find_one_and_update(
        filter={
            '_id': lesson_id_obj,
            'status': 'available',
            'date': {'$gt': now},
        },
        update={
            '$set': {
                'status': 'booked',
                'student_id': student_id,
            }
        },
        return_document=True,  # вернуть документ после обновления
    )

    if result is None:
        # Проверим, существует ли занятие вообще
        lesson_exists = lessons_collection.find_one({'_id': lesson_id_obj})
        if lesson_exists is None:
            logger.warning(f"Lesson not found: {lesson_id}")
            return {'success': False, 'error': 'Занятие не найдено'}
        elif lesson_exists.get('status') != 'available':
            logger.info(f"Lesson {lesson_id} already booked/cancelled")
            return {'success': False, 'error': 'Это занятие уже недоступно'}
        elif lesson_exists.get('date', now) <= now:
            logger.info(f"Lesson {lesson_id} is in the past")
            return {'success': False, 'error': 'Нельзя записаться на прошедшее занятие'}
        else:
            logger.warning(f"Atomic update failed for lesson {lesson_id} (unknown reason)")
            return {'success': False, 'error': 'Не удалось записаться (возможно, занятие уже занято)'}

    logger.info(f"Lesson {lesson_id} successfully booked by student {student_id}")
    return {'success': True, 'lesson': result}


def revoke_refresh_token(jti, expires_at=None):
    """
    Добавляет jti (JWT ID) refresh-токена в чёрный список.
    Храним в MongoDB коллекции `token_blacklist`, т.к.
    штатный модуль simplejwt требует SQL-миграций, несовместимых с djongo.

    Параметры:
        jti (str): уникальный ID токена
        expires_at (datetime, optional): когда токен истекает (для очистки устаревших)
    """
    from datetime import datetime

    blacklist_collection = get_mongo_collection('token_blacklist')

    try:
        blacklist_collection.update_one(
            {'jti': jti},
            {'$set': {'jti': jti, 'revoked_at': datetime.utcnow(), 'expires_at': expires_at}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to revoke token {jti}: {e}")
        return False


def is_token_revoked(jti):
    """Проверяет, отозван ли токен"""
    blacklist_collection = get_mongo_collection('token_blacklist')
    return blacklist_collection.find_one({'jti': jti}) is not None


def atomic_cancel_booking(lesson_id, student_id):
    """
    Атомарная отмена записи ученика.
    find_one_and_update с проверкой: student_id совпадает и status == 'booked'
    """
    lessons_collection = get_mongo_collection('lessons')

    try:
        lesson_id_obj = ObjectId(lesson_id)
    except Exception as e:
        logger.error(f"Invalid lesson_id format: {lesson_id} - {e}")
        return {'success': False, 'error': 'Неверный формат ID занятия'}

    result = lessons_collection.find_one_and_update(
        filter={
            '_id': lesson_id_obj,
            'student_id': student_id,
            'status': 'booked',
        },
        update={
            '$set': {
                'status': 'available',
                'student_id': None,
            }
        },
        return_document=True,
    )

    if result is None:
        return {'success': False, 'error': 'Запись не найдена или уже отменена'}
    return {'success': True, 'lesson': result}