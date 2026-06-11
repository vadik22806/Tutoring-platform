from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from bson import ObjectId

from .serializers import (
    SubjectSerializer, UserSerializer, LessonSerializer,
    SavedLessonSerializer, BookingGroupSerializer,
    RegisterSerializer, LoginSerializer, ProfileUpdateSerializer
)
from .utils import atomic_book_lesson, atomic_cancel_booking, revoke_refresh_token, is_token_revoked, get_mongo_collection
from .permissions import IsStudent, IsTutor, IsAdmin, IsOwnerOrAdmin, IsLessonOwner, IsBookingOwner
from main.models import Subject, User, Lesson, SavedLesson, BookingGroup


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_tokens_for_user(user):
    """Генерирует JWT токены для пользователя"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ========== ПРОВЕРКА РАБОТОСПОСОБНОСТИ ==========

class PingView(APIView):
    """Простой view для проверки работоспособности API"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok', 'message': 'API is up'})


# ========== АВТОРИЗАЦИЯ ==========

class RegisterView(APIView):
    """Регистрация нового пользователя (ученика или репетитора)"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            user_data = UserSerializer(user).data

            return Response({
                'user': user_data,
                'tokens': tokens,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Registration error: {e}")
            return Response(
                {'error': 'Ошибка при регистрации'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """Вход по email или телефону, возвращает JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({'error': 'Неверный email/телефон или пароль'}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            'user': user_data,
            'tokens': tokens,
        })


class LogoutView(APIView):
    """Выход из системы (инвалидация refresh токена)
    
    Отзывает refresh-токен через кастомный Mongo-блоклист,
    т.к. штатный simplejwt blacklist требует SQL-миграций.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'message': 'Выход выполнен'}, status=200)

        try:
            token = RefreshToken(refresh_token)
            jti = token.payload.get('jti')
            exp = token.payload.get('exp')
            
            from datetime import datetime
            expires_at = datetime.fromtimestamp(exp) if exp else None
            
            success = revoke_refresh_token(jti, expires_at)
            
            if success:
                return Response({'message': 'Выход выполнен успешно'})
            else:
                return Response({'message': 'Выход выполнен (токен не отозван)'}, status=200)
                
        except Exception as e:
            # Логируем ошибку, но не возвращаем 500 — пользователь всё равно выходит
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Logout error: {e}")
            return Response({'message': 'Выход выполнен'}, status=200)


class TokenRefreshRevokeView(APIView):
    """Обновление access-токена с проверкой blacklist
    
    Проверяет, не отозван ли refresh-токен через кастомный Mongo blacklist.
    Если токен отозван (logout), возвращает 401.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Не указан refresh токен'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            jti = token.payload.get('jti')

            # Проверяем, не отозван ли токен
            if is_token_revoked(jti):
                return Response(
                    {'error': 'Токен отозван. Выполните вход заново'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Генерируем новый access-токен
            new_access = str(token.access_token)
            return Response({'access': new_access})

        except TokenError as e:
            return Response(
                {'error': f'Недействительный токен: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Token refresh error: {e}")
            return Response(
                {'error': 'Ошибка при обновлении токена'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MeView(APIView):
    """Текущий авторизованный пользователь"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ========== ПОЛЬЗОВАТЕЛИ ==========

class TutorListView(generics.ListAPIView):
    """Список всех репетиторов"""
    queryset = User.objects.filter(role='tutor')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserDetailView(generics.RetrieveAPIView):
    """Профиль пользователя по ID"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_object(self):
        user_id = self.kwargs.get('id')
        try:
            return User.objects.get(_id=ObjectId(user_id))
        except User.DoesNotExist:
            return None
        except Exception:
            return None


class UserUpdateView(APIView):
    """Редактирование профиля пользователя"""
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def put(self, request, id):
        try:
            user = User.objects.get(_id=ObjectId(id))
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверка прав через permission-класс
        self.check_object_permissions(request, user)

        serializer = ProfileUpdateSerializer(data=request.data, instance_user=user)
        
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        updated_user = serializer.update_instance(user)
        user_data = UserSerializer(updated_user).data
        return Response(user_data)


# ========== ЗАНЯТИЯ ==========

class AvailableLessonsView(generics.ListAPIView):
    """Список доступных занятий (только будущие)"""
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        now = timezone.now()
        return Lesson.objects.filter(
            status='available',
            date__gt=now
        ).order_by('date')


class LessonListCreateView(generics.ListCreateAPIView):
    """Список всех занятий и создание нового занятия"""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsTutor()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = Lesson.objects.all().order_by('-date')

        # Фильтрация по репетитору
        tutor_id = self.request.query_params.get('tutor_id')
        if tutor_id:
            queryset = queryset.filter(tutor_id=tutor_id)

        # Фильтрация по ученику
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтрация по предмету
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(tutor_id=str(self.request.user._id), status='available')


# ========== РЕДАКТИРОВАНИЕ/УДАЛЕНИЕ ЗАНЯТИЯ ==========

class LessonDetailView(APIView):
    """Детали занятия, редактирование, удаление"""
    permission_classes = [IsLessonOwner]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsLessonOwner()]

    def get(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
            serializer = LessonSerializer(lesson)
            return Response(serializer.data)
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

    def put(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        # Проверка прав через permission-класс
        self.check_object_permissions(request, lesson)

        if lesson.status != 'available':
            return Response({'error': 'Нельзя редактировать занятие, на которое кто-то записан'}, status=400)

        data = request.data
        if 'subject_id' in data:
            lesson.subject_id = data['subject_id']
        if 'date' in data:
            lesson.date = data['date']
        if 'duration' in data:
            lesson.duration = data['duration']
        if 'price' in data:
            lesson.price = data['price']

        lesson.save()
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)

    def delete(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        # Проверка прав через permission-класс
        self.check_object_permissions(request, lesson)

        if lesson.status != 'available':
            return Response({'error': 'Нельзя удалить занятие, на которое кто-то записан'}, status=400)

        lesson.delete()
        return Response({'message': 'Занятие удалено'})


class CompleteLessonView(APIView):
    """Завершить занятие"""
    permission_classes = [IsAuthenticated, IsLessonOwner]

    def post(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        # Проверка прав через permission-класс
        self.check_object_permissions(request, lesson)

        if lesson.status != 'booked':
            return Response({'error': 'Можно завершить только забронированное занятие'}, status=400)

        lesson.status = 'completed'
        lesson.save()
        return Response({'message': 'Занятие отмечено как завершенное'})


class CancelLessonView(APIView):
    """Отменить занятие (репетитор)"""
    permission_classes = [IsAuthenticated, IsLessonOwner]

    def post(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        # Проверка прав через permission-класс
        self.check_object_permissions(request, lesson)

        if lesson.status != 'booked':
            return Response({'error': 'Можно отменить только забронированное занятие'}, status=400)

        lesson.status = 'cancelled'
        lesson.student_id = None
        lesson.save()
        return Response({'message': 'Занятие отменено'})


# ========== ЗАПИСИ (BOOKINGS) ==========

class BookLessonView(APIView):
    """Записаться на занятие (только ученик) — атомарно"""
    permission_classes = [IsStudent]

    def post(self, request):

        lesson_id = request.data.get('lesson_id')
        if not lesson_id:
            return Response({'error': 'Не указан lesson_id'}, status=400)

        # Проверка на конфликт по времени (неатомарная, но приемлемая проверка)
        try:
            lesson_check = Lesson.objects.get(_id=ObjectId(lesson_id))
            conflicting = Lesson.objects.filter(
                student_id=str(request.user._id),
                status='booked',
                date=lesson_check.date
            ).exists()
            if conflicting:
                return Response({'error': 'У вас уже есть занятие на это время'}, status=400)
        except Lesson.DoesNotExist:
            pass

        # Атомарная запись через PyMongo
        result = atomic_book_lesson(lesson_id, str(request.user._id))

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        # Удаляем из отложенных, если было
        SavedLesson.objects.filter(
            student_id=str(request.user._id),
            lesson_id=lesson_id
        ).delete()

        # Возвращаем обновлённое занятие через сериализатор
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)


class CancelBookingView(APIView):
    """Отменить запись (ученик) — атомарно"""
    permission_classes = [IsBookingOwner]

    def post(self, request, id):
        if request.user.role == 'admin' and not request.data.get('student_id'):
            # Для админов нужно передать student_id
            return Response({'error': 'Администратор должен указать student_id'}, status=400)

        student_id = str(request.user._id) if request.user.role == 'student' else request.data.get('student_id', str(request.user._id))

        result = atomic_cancel_booking(id, student_id)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Запись отменена'})


class MyBookingsView(APIView):
    """История записей ученика"""
    permission_classes = [IsStudent]

    def get(self, request):

        lessons = Lesson.objects.filter(
            student_id=str(request.user._id)
        ).order_by('-date')

        serializer = LessonSerializer(lessons, many=True)
        data = serializer.data

        # Считаем статистику
        total_spent = sum(l.price for l in lessons if l.status in ('completed', 'booked'))
        completed_count = lessons.filter(status='completed').count()
        upcoming_count = lessons.filter(status='booked', date__gt=timezone.now()).count()

        return Response({
            'lessons': data,
            'stats': {
                'total_spent': total_spent,
                'completed_count': completed_count,
                'upcoming_count': upcoming_count,
                'total_count': len(data),
            }
        })


# ========== ИЗБРАННОЕ (SAVED) ==========

class SavedLessonListView(APIView):
    """Список избранных занятий ученика"""
    permission_classes = [IsStudent]

    def get(self, request):

        saved_ids = SavedLesson.objects.filter(
            student_id=str(request.user._id)
        ).order_by('-added_at').values_list('lesson_id', flat=True)

        lessons = []
        total_price = 0
        for lesson_id in saved_ids:
            try:
                lesson = Lesson.objects.get(_id=ObjectId(lesson_id))
                if lesson.status == 'available':
                    total_price += lesson.price
                lessons.append(lesson)
            except Lesson.DoesNotExist:
                SavedLesson.objects.filter(lesson_id=lesson_id).delete()

        serializer = LessonSerializer(lessons, many=True)
        return Response({
            'lessons': serializer.data,
            'total_price': total_price,
            'count': len(lessons)
        })


class SaveLessonView(APIView):
    """Добавить занятие в избранное"""
    permission_classes = [IsStudent]

    def post(self, request, id):

        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        if lesson.status != 'available':
            return Response({'error': 'Это занятие уже недоступно'}, status=400)

        existing, created = SavedLesson.objects.get_or_create(
            student_id=str(request.user._id),
            lesson_id=id
        )

        if created:
            return Response({'message': 'Занятие добавлено в избранное'}, status=201)
        else:
            return Response({'message': 'Занятие уже в избранном'})


class UnsaveLessonView(APIView):
    """Удалить занятие из избранного"""
    permission_classes = [IsStudent]

    def delete(self, request, id):

        deleted = SavedLesson.objects.filter(
            student_id=str(request.user._id),
            lesson_id=id
        ).delete()

        if deleted[0] > 0:
            return Response({'message': 'Занятие удалено из избранного'})
        else:
            return Response({'message': 'Занятие не найдено в избранном'}, status=404)


class BookAllSavedView(APIView):
    """Записаться на все избранные занятия"""
    permission_classes = [IsStudent]

    def post(self, request):

        saved_ids = SavedLesson.objects.filter(
            student_id=str(request.user._id)
        ).values_list('lesson_id', flat=True)

        if not saved_ids:
            return Response({'error': 'У вас нет избранных занятий'}, status=400)

        now = timezone.now()
        booked_ids = []
        failed_lessons = []

        # Создаем группу заказа
        booking_group = BookingGroup.objects.create(
            student_id=str(request.user._id),
            total_price=0,
            lessons_count=0
        )

        for lesson_id in saved_ids:
            # Атомарная запись через find_one_and_update
            result = atomic_book_lesson(lesson_id, str(request.user._id))

            if result['success']:
                booking_group.lessons_count += 1
                booking_group.total_price += result['lesson'].get('price', 0)
                booked_ids.append(lesson_id)
            else:
                failed_lessons.append({
                    'lesson_id': lesson_id,
                    'error': result['error']
                })

        booking_group.save()

        # Удаляем из saved только успешно забронированные
        if booked_ids:
            SavedLesson.objects.filter(
                student_id=str(request.user._id),
                lesson_id__in=booked_ids
            ).delete()

        result = {
            'booked': len(booked_ids),
            'failed': len(failed_lessons),
            'booked_ids': booked_ids,
            'failed_details': failed_lessons[:5],
        }
        if len(booked_ids) > 0:
            result['booking_group_id'] = booking_group.id

        return Response(result)


# ========== ПРЕДМЕТЫ ==========

class SubjectListView(generics.ListAPIView):
    """Список всех предметов"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]


# ========== УЧЕНИКИ ==========

class StudentListView(generics.ListAPIView):
    """Список всех учеников"""
    queryset = User.objects.filter(role='student')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


# ========== ДАШБОРДЫ ==========

class DashboardView(APIView):
    """Данные для личного кабинета (дашборда) — оптимизированная версия
    
    Использует пакетную загрузку и MongoDB агрегаты вместо Python-циклов.
    Для рекомендаций репетиторов — использует агрегатный запрос с $lookup.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        
        # Пакетная загрузка всех предметов (один запрос вместо десятков)
        all_subjects = Subject.objects.all()
        subjects_dict = {str(s._id): s.name for s in all_subjects}

        if user.role == 'tutor':
            return self._tutor_dashboard(user, subjects_dict)
        elif user.role == 'student':
            return self._student_dashboard(user, subjects_dict, now)
        return Response({'error': 'Неизвестная роль'}, status=400)

    def _tutor_dashboard(self, user, subjects_dict):
        """Дашборд репетитора — один запрос к БД со статистикой"""
        user_id = str(user._id)
        
        # Получаем статистику через MongoDB агрегат
        lessons_collection = get_mongo_collection('lessons')
        
        pipeline = [
            {'$match': {'tutor_id': user_id}},
            {'$group': {
                '_id': None,
                'total': {'$sum': 1},
                'available': {'$sum': {'$cond': [{'$eq': ['$status', 'available']}, 1, 0]}},
                'booked': {'$sum': {'$cond': [{'$eq': ['$status', 'booked']}, 1, 0]}},
                'completed': {'$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}},
            }}
        ]
        
        stats_result = list(lessons_collection.aggregate(pipeline))
        
        # Предметы репетитора (из subject_ids)
        tutor_subjects = []
        if user.subject_ids:
            for sid in user.subject_ids:
                if sid in subjects_dict:
                    tutor_subjects.append({'id': sid, 'name': subjects_dict[sid]})

        stats = stats_result[0] if stats_result else {}
        
        return Response({
            'role': 'tutor',
            'user': UserSerializer(user).data,
            'subjects': tutor_subjects,
            'stats': {
                'total': stats.get('total', 0),
                'available': stats.get('available', 0),
                'booked': stats.get('booked', 0),
                'completed': stats.get('completed', 0),
            }
        })

    def _student_dashboard(self, user, subjects_dict, now):
        """Дашборд ученика — пакетная загрузка всех данных"""
        user_id = str(user._id)
        student_subject_ids = user.subject_ids if user.subject_ids else []

        # Параллельные запросы (все 5 за раз через MongoDB агрегат)
        
        # 1. Доступные занятия (первые 5)
        available_lessons = list(Lesson.objects.filter(
            status='available', date__gt=now
        ).order_by('date')[:5])

        # 2. Мои предстоящие занятия
        my_lessons = list(Lesson.objects.filter(
            student_id=user_id, status='booked', date__gt=now
        ).order_by('date')[:5])

        # 3. Отложенные занятия
        saved_ids = list(SavedLesson.objects.filter(
            student_id=user_id
        ).values_list('lesson_id', flat=True))
        
        saved_lessons = []
        if saved_ids:
            saved_lessons = list(Lesson.objects.filter(
                _id__in=[ObjectId(id) for id in saved_ids]
            ))

        # 4. Рекомендуемые репетиторы — через MongoDB агрегат с Lookup
        #    (вместо Python-цикла по всем репетиторам)
        recommended_tutors = self._get_recommended_tutors(
            student_subject_ids, subjects_dict
        )
        
        # 5. Статистика
        total_booked = Lesson.objects.filter(
            student_id=user_id, status='booked'
        ).count()
        completed_count = Lesson.objects.filter(
            student_id=user_id, status='completed'
        ).count()

        # Обогащаем занятия именами и предметами пакетно
        tutor_ids = set()
        for lesson in available_lessons + my_lessons + saved_lessons:
            if lesson.tutor_id:
                tutor_ids.add(ObjectId(lesson.tutor_id))
        
        # Пакетная загрузка репетиторов (один запрос вместо N)
        tutors_map = {}
        if tutor_ids:
            tutors = User.objects.filter(_id__in=list(tutor_ids))
            tutors_map = {str(t._id): f"{t.first_name} {t.last_name}" for t in tutors}

        def enrich_lesson(lesson):
            data = LessonSerializer(lesson).data
            data['subject_name'] = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
            data['tutor_name'] = tutors_map.get(lesson.tutor_id, None)
            return data

        return Response({
            'role': 'student',
            'user': UserSerializer(user).data,
            'available_lessons': [enrich_lesson(l) for l in available_lessons],
            'my_lessons': [enrich_lesson(l) for l in my_lessons],
            'saved_lessons': [enrich_lesson(l) for l in saved_lessons],
            'recommended_tutors': recommended_tutors,
            'stats': {
                'total': total_booked,
                'completed': completed_count,
                'interests': len(student_subject_ids),
                'saved': len(saved_lessons),
            }
        })

    def _get_recommended_tutors(self, student_subject_ids, subjects_dict):
        """
        Поиск рекомендуемых репетиторов через MongoDB агрегат.
        Использует $lookup + $match по интересам ученика.
        """
        if not student_subject_ids:
            return []
        
        # Используем агрегат для поиска репетиторов с совпадающими предметами
        users_collection = get_mongo_collection('users')
        
        pipeline = [
            {'$match': {'role': 'tutor', 'subject_ids': {'$in': student_subject_ids}}},
            {'$addFields': {
                'common_count': {
                    '$size': {
                        '$filter': {
                            'input': '$subject_ids',
                            'as': 'sid',
                            'cond': {'$in': ['$$sid', student_subject_ids]}
                        }
                    }
                }
            }},
            {'$sort': {'common_count': -1, 'rating': -1}},
            {'$limit': 3},
            {'$project': {
                '_id': {'$toString': '$_id'},
                'first_name': 1,
                'last_name': 1,
                'rating': 1,
                'bio': 1,
                'subject_ids': 1,
            }}
        ]
        
        try:
            tutors = list(users_collection.aggregate(pipeline))
        except Exception:
            return []
        
        result = []
        for t in tutors:
            common = []
            tutor_names = []
            for sid in (t.get('subject_ids') or []):
                sid_str = str(sid)
                if sid_str in subjects_dict:
                    if sid_str in student_subject_ids:
                        common.append(subjects_dict[sid_str])
                    tutor_names.append(subjects_dict[sid_str])
            
            result.append({
                'id': t.get('_id'),
                'first_name': t.get('first_name', ''),
                'last_name': t.get('last_name', ''),
                'rating': t.get('rating'),
                'bio': t.get('bio', ''),
                'common_subjects': common,
                'subject_names': tutor_names,
            })
        
        return result


# ========== AJAX ПРОВЕРКИ ==========

class CheckEmailView(APIView):
    """Проверка уникальности email"""
    permission_classes = [AllowAny]

    def get(self, request):
        email = request.query_params.get('email', '')
        if not email:
            return Response({'exists': False})
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists})


class CheckPhoneView(APIView):
    """Проверка уникальности телефона"""
    permission_classes = [AllowAny]

    def get(self, request):
        phone = request.query_params.get('phone', '')
        if not phone:
            return Response({'exists': False})
        import re
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        exists = User.objects.filter(phone=cleaned).exists()
        return Response({'exists': exists})


# ========== ТЕСТОВЫЙ ЭНДПОИНТ ==========

class DebugAuthView(APIView):
    """Проверка авторизации (для тестов)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'authenticated': True,
            'user_id': str(request.user._id),
            'email': request.user.email,
            'role': request.user.role,
        })