"""
Management command для очистки устаревших записей в token_blacklist.

Удаляет записи, у которых expires_at меньше текущего времени.
Запуск: python manage.py cleanup_token_blacklist

Опционально: --dry-run (только показать, сколько будет удалено)
            --age N (удалить записи старше N дней, по умолчанию — все просроченные)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.utils import get_mongo_collection


class Command(BaseCommand):
    help = 'Очищает устаревшие записи в token_blacklist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать количество записей для удаления, не удалять',
        )
        parser.add_argument(
            '--age',
            type=int,
            default=0,
            help='Удалить записи старше N дней (0 = все просроченные)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        age = options['age']
        now = timezone.now()

        collection = get_mongo_collection('token_blacklist')

        # Формируем фильтр
        if age > 0:
            cutoff = now - timedelta(days=age)
            filter_query = {
                '$or': [
                    {'expires_at': {'$lt': cutoff}},
                    {'expires_at': {'$exists': False}},
                    {'expires_at': None},
                ]
            }
            label = f"старше {age} дней (или без expires_at)"
        else:
            filter_query = {
                '$or': [
                    {'expires_at': {'$lt': now}},
                    {'expires_at': {'$exists': False}},
                    {'expires_at': None},
                ]
            }
            label = "просроченные (или без expires_at)"

        # Считаем
        count = collection.count_documents(filter_query)

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"Нет {label} записей для удаления"))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[DRY-RUN] Будет удалено {count} {label} записей")
            )
            return

        # Удаляем
        result = collection.delete_many(filter_query)
        self.stdout.write(
            self.style.SUCCESS(
                f"Удалено {result.deleted_count} {label} записей из token_blacklist"
            )
        )