from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from bson import ObjectId

from .serializers import (
    SubjectSerializer, UserSerializer, LessonSerializer,
    SavedLessonSerializer, BookingGroupSerializer
)
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
        data = request.data

        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'student')
        bio = data.get('bio', '').strip()
        subjects = data.get('subjects', [])

        # Валидация
        errors = {}

        if not first_name:
            errors['first_name'] = 'Имя обязательно'

        if not email and not phone:
            errors['email'] = 'Укажите email или номер телефона'
            errors['phone'] = 'Укажите email или номер телефона'

        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'Пользователь с таким email уже существует'

        if phone:
            import re
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if User.objects.filter(phone=cleaned_phone).exists():
                errors['phone'] = 'Пользователь с таким телефоном уже существует'

        if len(password) < 6:
            errors['password'] = 'Пароль должен быть минимум 6 символов'

        if password != password_confirm:
            errors['password_confirm'] = 'Пароли не совпадают'

        if role not in ['student', 'tutor']:
            errors['role'] = 'Роль должна быть student или tutor'

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем пользователя
        try:
            user = User(
                email=email if email else None,
                phone=cleaned_phone if phone else None,
                first_name=first_name,
                last_name=last_name,
                role=role,
                bio=bio,
                subject_ids=list(subjects) if subjects else [],
            )
            user.set_password(password)
            user.save()

            tokens = get_tokens_for_user(user)
            serializer = UserSerializer(user)

            return Response({
                'user': serializer.data,
                'tokens': tokens,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Ошибка при регистрации: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """Вход по email или телефону, возвращает JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'error': 'Укажите email/телефон и пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Неверный email/телефон или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = get_tokens_for_user(user)
        serializer = UserSerializer(user)

        return Response({
            'user': serializer.data,
            'tokens': tokens,
        })


class LogoutView(APIView):
    """Выход из системы (инвалидация refresh токена)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'message': 'Выход выполнен успешно'})
            else:
                return Response({'message': 'Выход выполнен'})
        except Exception as e:
            return Response(
                {'error': f'Ошибка при выходе: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
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
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        # Проверяем, что пользователь редактирует свой профиль
        if str(request.user._id) != id and request.user.role != 'admin':
            return Response(
                {'error': 'Вы можете редактировать только свой профиль'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(_id=ObjectId(id))
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data

        # Разрешенные поля для обновления
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'bio' in data:
            user.bio = data['bio'].strip()
        if 'subject_ids' in data:
            user.subject_ids = list(data['subject_ids'])
        if 'email' in data:
            email = data['email'].strip()
            if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
                return Response(
                    {'error': 'Пользователь с таким email уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = email if email else None
        if 'phone' in data:
            import re
            phone = data['phone'].strip()
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if cleaned_phone and User.objects.filter(phone=cleaned_phone).exclude(pk=user.pk).exists():
                return Response(
                    {'error': 'Пользователь с таким телефоном уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.phone = cleaned_phone if cleaned_phone else None

        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data)


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
        # Проверяем, что пользователь — репетитор
        if self.request.user.role != 'tutor':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Только репетиторы могут создавать занятия')

        serializer.save(tutor_id=str(self.request.user._id), status='available')


# ========== РЕДАКТИРОВАНИЕ/УДАЛЕНИЕ ЗАНЯТИЯ ==========

class LessonDetailView(APIView):
    """Детали занятия, редактирование, удаление"""
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

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

        # Только репетитор-владелец или админ
        if lesson.tutor_id != str(request.user._id) and request.user.role != 'admin':
            return Response({'error': 'Это не ваше занятие'}, status=403)

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

        if lesson.tutor_id != str(request.user._id) and request.user.role != 'admin':
            return Response({'error': 'Это не ваше занятие'}, status=403)

        if lesson.status != 'available':
            return Response({'error': 'Нельзя удалить занятие, на которое кто-то записан'}, status=400)

        lesson.delete()
        return Response({'message': 'Занятие удалено'})


class CompleteLessonView(APIView):
    """Завершить занятие"""
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        if lesson.tutor_id != str(request.user._id) and request.user.role != 'admin':
            return Response({'error': 'Это не ваше занятие'}, status=403)

        if lesson.status != 'booked':
            return Response({'error': 'Можно завершить только забронированное занятие'}, status=400)

        lesson.status = 'completed'
        lesson.save()
        return Response({'message': 'Занятие отмечено как завершенное'})


class CancelLessonView(APIView):
    """Отменить занятие (репетитор)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        if lesson.tutor_id != str(request.user._id) and request.user.role != 'admin':
            return Response({'error': 'Это не ваше занятие'}, status=403)

        if lesson.status != 'booked':
            return Response({'error': 'Можно отменить только забронированное занятие'}, status=400)

        lesson.status = 'cancelled'
        lesson.student_id = None
        lesson.save()
        return Response({'message': 'Занятие отменено'})


# ========== ЗАПИСИ (BOOKINGS) ==========

class BookLessonView(APIView):
    """Записаться на занятие (только ученик)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Только ученики могут записываться'}, status=403)

        lesson_id = request.data.get('lesson_id')
        if not lesson_id:
            return Response({'error': 'Не указан lesson_id'}, status=400)

        try:
            lesson = Lesson.objects.get(_id=ObjectId(lesson_id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        if lesson.status != 'available':
            return Response({'error': 'Это занятие уже недоступно'}, status=400)

        if lesson.date < timezone.now():
            return Response({'error': 'Нельзя записаться на прошедшее занятие'}, status=400)

        # Проверка на конфликт по времени
        conflicting = Lesson.objects.filter(
            student_id=str(request.user._id),
            status='booked',
            date=lesson.date
        ).exists()
        if conflicting:
            return Response({'error': 'У вас уже есть занятие на это время'}, status=400)

        lesson.student_id = str(request.user._id)
        lesson.status = 'booked'
        lesson.save()

        # Удаляем из отложенных, если было
        SavedLesson.objects.filter(
            student_id=str(request.user._id),
            lesson_id=lesson_id
        ).delete()

        serializer = LessonSerializer(lesson)
        return Response(serializer.data)


class CancelBookingView(APIView):
    """Отменить запись (ученик)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            lesson = Lesson.objects.get(_id=ObjectId(id))
        except Lesson.DoesNotExist:
            return Response({'error': 'Занятие не найдено'}, status=404)

        if lesson.student_id != str(request.user._id) and request.user.role != 'admin':
            return Response({'error': 'Это не ваша запись'}, status=403)

        if lesson.status != 'booked':
            return Response({'error': 'Можно отменить только забронированное занятие'}, status=400)

        lesson.student_id = None
        lesson.status = 'available'
        lesson.save()
        return Response({'message': 'Запись отменена'})


class MyBookingsView(APIView):
    """История записей ученика"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Только для учеников'}, status=403)

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Только для учеников'}, status=403)

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
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        if request.user.role != 'student':
            return Response({'error': 'Только ученики могут добавлять в избранное'}, status=403)

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
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        if request.user.role != 'student':
            return Response({'error': 'Только ученики могут управлять избранным'}, status=403)

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Только ученики могут записываться'}, status=403)

        saved_ids = SavedLesson.objects.filter(
            student_id=str(request.user._id)
        ).values_list('lesson_id', flat=True)

        if not saved_ids:
            return Response({'error': 'У вас нет избранных занятий'}, status=400)

        now = timezone.now()
        booked_count = 0
        failed_lessons = []

        # Создаем группу заказа
        booking_group = BookingGroup.objects.create(
            student_id=str(request.user._id),
            total_price=0,
            lessons_count=0
        )

        for lesson_id in saved_ids:
            try:
                lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

                if lesson.status != 'available':
                    failed_lessons.append(f"{lesson_id} (уже недоступно)")
                    continue
                if lesson.date < now:
                    failed_lessons.append(f"{lesson_id} (прошедшее)")
                    continue

                conflicting = Lesson.objects.filter(
                    student_id=str(request.user._id),
                    status='booked',
                    date=lesson.date
                ).exists()
                if conflicting:
                    failed_lessons.append(f"{lesson_id} (конфликт)")
                    continue

                lesson.student_id = str(request.user._id)
                lesson.status = 'booked'
                lesson.save()

                booking_group.lessons_count += 1
                booking_group.total_price += lesson.price
                booked_count += 1

            except Exception:
                failed_lessons.append(f"{lesson_id} (ошибка)")

        booking_group.save()
        SavedLesson.objects.filter(student_id=str(request.user._id)).delete()

        result = {'booked': booked_count}
        if failed_lessons:
            result['failed'] = len(failed_lessons)
            result['failed_details'] = failed_lessons[:3]
        if booked_count > 0:
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
    """Данные для личного кабинета (дашборда)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        subjects_dict = {str(s._id): s.name for s in Subject.objects.all()}

        if user.role == 'tutor':
            # Занятия репетитора
            my_lessons = Lesson.objects.filter(tutor_id=str(user._id)).order_by('date')

            # Предметы репетитора
            tutor_subjects = []
            if user.subject_ids:
                for sid in user.subject_ids:
                    if sid in subjects_dict:
                        tutor_subjects.append({'id': sid, 'name': subjects_dict[sid]})

            # Статистика
            total = my_lessons.count()
            available = my_lessons.filter(status='available').count()
            booked = my_lessons.filter(status='booked').count()
            completed = my_lessons.filter(status='completed').count()

            return Response({
                'role': 'tutor',
                'user': UserSerializer(user).data,
                'subjects': tutor_subjects,
                'stats': {
                    'total': total,
                    'available': available,
                    'booked': booked,
                    'completed': completed,
                }
            })

        elif user.role == 'student':
            # Доступные занятия (первые 5)
            available_lessons = Lesson.objects.filter(
                status='available', date__gt=now
            ).order_by('date')[:5]

            # Мои предстоящие занятия
            my_lessons = Lesson.objects.filter(
                student_id=str(user._id), status='booked', date__gt=now
            ).order_by('date')[:5]

            # Отложенные
            saved_ids = SavedLesson.objects.filter(
                student_id=str(user._id)
            ).values_list('lesson_id', flat=True)
            saved_lessons = Lesson.objects.filter(_id__in=[ObjectId(id) for id in saved_ids])

            # Рекомендуемые репетиторы (по интересам ученика)
            student_subject_ids = user.subject_ids if user.subject_ids else []
            all_tutors = User.objects.filter(role='tutor')
            recommended_tutors = []

            for tutor in all_tutors:
                if tutor.subject_ids:
                    common = []
                    for sid in student_subject_ids:
                        if sid in tutor.subject_ids:
                            name = subjects_dict.get(str(sid), 'Неизвестный предмет')
                            common.append(name)
                    if common:
                        tutor_names = []
                        for sid in tutor.subject_ids:
                            name = subjects_dict.get(str(sid), 'Неизвестный предмет')
                            tutor_names.append(name)
                        recommended_tutors.append({
                            'id': tutor.id,
                            'first_name': tutor.first_name,
                            'last_name': tutor.last_name,
                            'rating': tutor.rating,
                            'bio': tutor.bio,
                            'common_subjects': common,
                            'subject_names': tutor_names,
                        })

            recommended_tutors.sort(key=lambda x: x.get('rating') or 0, reverse=True)
            recommended_tutors = recommended_tutors[:3]

            # Статистика
            total_booked = Lesson.objects.filter(
                student_id=str(user._id), status='booked'
            ).count()
            completed_count = Lesson.objects.filter(
                student_id=str(user._id), status='completed'
            ).count()

            # Формируем данные с названиями предметов и именами
            def enrich_lesson(lesson):
                data = LessonSerializer(lesson).data
                data['subject_name'] = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
                try:
                    tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))
                    data['tutor_name'] = f"{tutor.first_name} {tutor.last_name}"
                except:
                    data['tutor_name'] = None
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
                    'saved': saved_lessons.count(),
                }
            })

        return Response({'error': 'Неизвестная роль'}, status=400)


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