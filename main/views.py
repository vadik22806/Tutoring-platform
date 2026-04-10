from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bson import ObjectId
import json
from .models import User, Subject, Lesson, SavedLesson, BookingGroup
from .forms import (
    StudentRegistrationForm,
    TutorRegistrationForm,
    LoginForm,
    LessonForm,
    EditProfileForm  # Добавили новую форму
)


def home(request):
    """Главная страница"""
    return render(request, 'main/home.html')


def about(request):
    """Страница о нас"""
    return render(request, 'main/about.html')


# ========== АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ==========

def login_choice(request):
    """Страница выбора роли для входа"""
    return render(request, 'main/login_choice.html')


def register_choice(request):
    """Страница выбора роли для регистрации"""
    return render(request, 'main/register_choice.html')


from django.contrib.auth import login
from .forms import LoginForm


def login_view(request):
    """Обработка входа по email ИЛИ телефону"""
    role = request.GET.get('role', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # user уже прошел аутентификацию в форме (authenticate)
            user = form.cleaned_data['user']

            # Проверяем роль
            if role and user.role != role:
                messages.error(request, f'Вы пытаетесь войти как {role}, но ваш аккаунт - {user.role}')
                return redirect('login_choice')

            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}!')

            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'tutor':
                return redirect('tutor_dashboard')
            else:
                return redirect('admin:index')
    else:
        form = LoginForm()

    return render(request, 'main/login.html', {'form': form, 'role': role})


def register_student(request):
    """Регистрация ученика"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # 👇 Добавь это
            from django.conf import settings
            user.backend = 'django.contrib.auth.backends.ModelBackend'

            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'main/register_student.html', {'form': form})


def register_tutor(request):
    """Регистрация репетитора"""
    if request.method == 'POST':
        form = TutorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # 👇 ВОТ ЭТО ВАЖНО - указываем бэкенд
            from django.conf import settings
            user.backend = 'django.contrib.auth.backends.ModelBackend'

            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')
            return redirect('tutor_dashboard')
    else:
        form = TutorRegistrationForm()

    return render(request, 'main/register_tutor.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('home')


# ========== ЛИЧНЫЙ КАБИНЕТ С РЕДАКТИРОВАНИЕМ ==========

@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user, user_role=request.user.role)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            if request.user.role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('tutor_dashboard')
    else:
        form = EditProfileForm(instance=request.user, user_role=request.user.role)

    return render(request, 'main/edit_profile.html', {'form': form})


# ========== ЛИЧНЫЕ КАБИНЕТЫ ==========

@login_required
def student_dashboard(request):
    """Личный кабинет ученика"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    from django.utils import timezone
    from bson import ObjectId

    # Получаем текущее время
    now = timezone.now()

    # ===== 1. ДОСТУПНЫЕ ЗАНЯТИЯ =====
    # Получаем доступные занятия (только будущие)
    available_lessons = Lesson.objects.filter(
        status='available',
        date__gt=now
    ).order_by('date')[:5]

    # ===== 2. ПРЕДСТОЯЩИЕ ЗАНЯТИЯ УЧЕНИКА =====
    # Получаем предстоящие занятия ученика
    my_lessons = Lesson.objects.filter(
        student_id=str(request.user._id),
        status='booked',
        date__gt=now
    ).order_by('date')[:5]

    # ===== 3. ОТЛОЖЕННЫЕ ЗАНЯТИЯ =====
    # Получаем ID отложенных занятий
    saved_lesson_ids = SavedLesson.objects.filter(
        student_id=str(request.user._id)
    ).values_list('lesson_id', flat=True)

    saved_lessons = Lesson.objects.filter(_id__in=[ObjectId(id) for id in saved_lesson_ids])

    # ===== 4. РЕКОМЕНДУЕМЫЕ РЕПЕТИТОРЫ =====
    # Получаем предметы, которые интересуют ученика
    student_subject_ids = request.user.subject_ids if request.user.subject_ids else []
    print(f"DEBUG - Student interests: {student_subject_ids}")

    # Получаем всех репетиторов
    all_tutors = User.objects.filter(role='tutor')

    # Получаем все предметы для отображения названий
    subjects_dict = {str(s._id): s.name for s in Subject.objects.all()}

    # Фильтруем репетиторов по предметам ученика
    recommended_tutors = []

    for tutor in all_tutors:
        if tutor.subject_ids:
            # Проверяем, есть ли у репетитора предметы, которые интересуют ученика
            common_subjects = []
            for subject_id in student_subject_ids:
                if subject_id in tutor.subject_ids:
                    # Добавляем название предмета для отображения
                    subject_name = subjects_dict.get(str(subject_id), 'Неизвестный предмет')
                    common_subjects.append(subject_name)

            # Если есть общие предметы, добавляем репетитора в рекомендации
            if common_subjects:
                tutor.common_subjects = common_subjects
                # Добавляем названия всех предметов репетитора
                tutor.subject_names = []
                for sid in tutor.subject_ids:
                    subject_name = subjects_dict.get(str(sid), 'Неизвестный предмет')
                    tutor.subject_names.append(subject_name)
                recommended_tutors.append(tutor)

    # Сортируем по рейтингу (от большего к меньшему)
    recommended_tutors.sort(key=lambda x: x.rating if x.rating else 0, reverse=True)

    # Берем только первых 3 репетиторов
    recommended_tutors = recommended_tutors[:3]

    print(f"DEBUG - Found {len(recommended_tutors)} recommended tutors")

    # ===== 5. ДОБАВЛЯЕМ ИНФОРМАЦИЮ К ЗАНЯТИЯМ =====
    # Добавляем названия предметов к доступным занятиям
    for lesson in available_lessons:
        lesson.subject_name = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
        try:
            lesson.tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))
        except:
            lesson.tutor = None

    # Добавляем названия предметов к занятиям ученика
    for lesson in my_lessons:
        lesson.subject_name = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
        try:
            lesson.tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))
        except:
            lesson.tutor = None

    # Добавляем названия предметов к отложенным занятиям
    for lesson in saved_lessons:
        lesson.subject_name = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
        try:
            lesson.tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))
        except:
            lesson.tutor = None

    # ===== 6. СТАТИСТИКА =====
    # Подсчитываем статистику для ученика
    total_my_lessons = Lesson.objects.filter(
        student_id=str(request.user._id),
        status='booked'
    ).count()

    completed_lessons = Lesson.objects.filter(
        student_id=str(request.user._id),
        status='completed'
    ).count()

    saved_count = saved_lessons.count()

    context = {
        'user': request.user,
        'available_lessons': available_lessons,
        'my_lessons': my_lessons,
        'saved_lessons': saved_lessons,
        'recommended_tutors': recommended_tutors,
        'saved_count': saved_count,
        'stats': {
            'total': total_my_lessons,
            'completed': completed_lessons,
            'interests': len(student_subject_ids),
            'saved': saved_count,
        }
    }

    return render(request, 'main/student_dashboard.html', context)


@login_required
def tutor_dashboard(request):
    """Личный кабинет репетитора"""
    if request.user.role != 'tutor':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    from datetime import datetime

    # Получаем занятия репетитора
    my_lessons = Lesson.objects.filter(
        tutor_id=str(request.user._id)
    ).order_by('date')

    # Получаем предметы репетитора
    tutor_subjects = []
    subjects_dict = {str(s._id): s for s in Subject.objects.all()}

    if request.user.subject_ids:
        for subject_id in request.user.subject_ids:
            if subject_id in subjects_dict:
                tutor_subjects.append(subjects_dict[subject_id])

    # Добавляем названия предметов к занятиям
    for lesson in my_lessons:
        if lesson.subject_id in subjects_dict:
            lesson.subject_name = subjects_dict[lesson.subject_id].name
        else:
            lesson.subject_name = 'Неизвестный предмет'

        if lesson.student_id:
            try:
                lesson.student = User.objects.get(_id=ObjectId(lesson.student_id))
            except:
                lesson.student = None

    # Статистика
    total_lessons = my_lessons.count()
    available = my_lessons.filter(status='available').count()
    booked = my_lessons.filter(status='booked').count()
    completed = my_lessons.filter(status='completed').count()

    context = {
        'user': request.user,
        'my_lessons': my_lessons,
        'tutor_subjects': tutor_subjects,
        'stats': {
            'total': total_lessons,
            'available': available,
            'booked': booked,
            'completed': completed,
        }
    }
    return render(request, 'main/tutor_dashboard.html', context)


# ========== РАБОТА С ОТЛОЖЕННЫМИ ЗАНЯТИЯМИ ==========

@login_required
def save_lesson(request, lesson_id):
    """Добавить занятие в отложенные"""
    if request.user.role != 'student':
        messages.error(request, 'Только ученики могут откладывать занятия')
        return redirect('home')

    # Получаем URL для возврата (если есть)
    next_url = request.GET.get('next')

    try:
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

        if lesson.status != 'available':
            messages.error(request, 'Это занятие уже недоступно')
            # Возвращаем на исходную страницу или на доступные занятия
            return redirect(next_url or 'available_lessons')

        existing, created = SavedLesson.objects.get_or_create(
            student_id=str(request.user._id),
            lesson_id=lesson_id
        )

        if created:
            messages.success(request, 'Занятие добавлено в избранное')
        else:
            messages.info(request, 'Это занятие уже в избранном')

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')

    # Возвращаем на исходную страницу
    if next_url:
        return redirect(next_url)

    # Если нет next_url, проверяем referer
    referer = request.META.get('HTTP_REFERER')
    if referer and 'student_dashboard' in referer:
        return redirect('student_dashboard')
    elif referer and 'saved_lessons' in referer:
        return redirect('saved_lessons')
    else:
        return redirect('available_lessons')


@login_required
def unsave_lesson(request, lesson_id):
    """Удалить занятие из отложенных"""
    if request.user.role != 'student':
        messages.error(request, 'Только ученики могут управлять избранным')
        return redirect('home')

    next_url = request.GET.get('next')

    try:
        saved = SavedLesson.objects.filter(
            student_id=str(request.user._id),
            lesson_id=lesson_id
        )

        if saved.exists():
            saved.delete()
            messages.success(request, 'Занятие удалено из избранного')
        else:
            messages.info(request, 'Занятие не найдено в избранном')

    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')

    # Возвращаем на исходную страницу
    if next_url:
        return redirect(next_url)

    # Если нет next_url, проверяем referer
    referer = request.META.get('HTTP_REFERER')
    if referer and 'student_dashboard' in referer:
        return redirect('student_dashboard')
    elif referer and 'saved_lessons' in referer:
        return redirect('saved_lessons')
    elif referer and 'available_lessons' in referer:
        return redirect('available_lessons')
    else:
        return redirect('student_dashboard')


@login_required
def saved_lessons(request):
    """Страница с отложенными занятиями (корзина)"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    # Получаем отложенные занятия
    saved_lesson_ids = SavedLesson.objects.filter(
        student_id=str(request.user._id)
    ).order_by('-added_at').values_list('lesson_id', flat=True)

    lessons = []
    subjects_dict = {str(s._id): s.name for s in Subject.objects.all()}
    total_price = 0

    for lesson_id in saved_lesson_ids:
        try:
            lesson = Lesson.objects.get(_id=ObjectId(lesson_id))
            lesson.subject_name = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
            lesson.tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))

            # Проверяем статус
            if lesson.status != 'available':
                lesson.unavailable = True
            else:
                lesson.unavailable = False
                total_price += lesson.price

            lessons.append(lesson)
        except:
            # Если занятие не найдено, удаляем его из отложенных
            SavedLesson.objects.filter(lesson_id=lesson_id).delete()

    context = {
        'lessons': lessons,
        'total_price': total_price,
        'count': len(lessons)
    }
    return render(request, 'main/saved_lessons.html', context)


@login_required
def book_all_saved(request):
    """Записаться на все отложенные занятия"""
    if request.user.role != 'student':
        messages.error(request, 'Только ученики могут записываться')
        return redirect('home')

    if request.method != 'POST':
        return redirect('saved_lessons')

    # Получаем отложенные занятия
    saved_lesson_ids = SavedLesson.objects.filter(
        student_id=str(request.user._id)
    ).values_list('lesson_id', flat=True)

    if not saved_lesson_ids:
        messages.info(request, 'У вас нет отложенных занятий')
        return redirect('saved_lessons')

    now = timezone.now()
    booked_count = 0
    failed_count = 0
    failed_lessons = []

    # Создаем группу для заказа
    booking_group = BookingGroup.objects.create(
        student_id=str(request.user._id),
        total_price=0,
        lessons_count=0
    )

    total_price = 0

    for lesson_id in saved_lesson_ids:
        try:
            lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

            # Проверки
            if lesson.status != 'available':
                failed_count += 1
                failed_lessons.append(f"{lesson.subject_name} (уже недоступно)")
                continue

            if lesson.date < now:
                failed_count += 1
                failed_lessons.append(f"{lesson.subject_name} (прошедшее)")
                continue

            # Проверка на конфликт по времени
            conflicting = Lesson.objects.filter(
                student_id=str(request.user._id),
                status='booked',
                date=lesson.date
            ).exists()

            if conflicting:
                failed_count += 1
                failed_lessons.append(f"{lesson.subject_name} (конфликт по времени)")
                continue

            # Записываем ученика
            lesson.student_id = str(request.user._id)
            lesson.status = 'booked'
            lesson.save()

            # Добавляем ID занятия в группу (через поле в Lesson или отдельную модель)
            # Пока просто увеличиваем счетчик
            booking_group.lessons_count += 1
            booking_group.total_price += lesson.price

            booked_count += 1

        except Exception as e:
            failed_count += 1
            failed_lessons.append(f"ID {lesson_id}: ошибка")

    # Обновляем группу
    booking_group.save()

    # Очищаем отложенные (удаляем все)
    SavedLesson.objects.filter(student_id=str(request.user._id)).delete()

    # Сообщаем результат
    if booked_count > 0:
        messages.success(request, f'✅ Успешно записано на {booked_count} занятий!')

    if failed_count > 0:
        messages.warning(request,
                         f'⚠️ Не удалось записаться на {failed_count} занятий: {", ".join(failed_lessons[:3])}')

    return redirect('saved_lessons')


# ========== ИСТОРИЯ ЗАПИСЕЙ ==========

@login_required
def my_bookings(request):
    """Страница с историей записей"""
    if request.user.role != 'student':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    # Получаем все занятия ученика
    all_lessons = Lesson.objects.filter(
        student_id=str(request.user._id)
    ).order_by('-date')

    # Группируем по месяцам для удобства
    from django.utils import timezone
    from datetime import datetime

    subjects_dict = {str(s._id): s.name for s in Subject.objects.all()}

    for lesson in all_lessons:
        lesson.subject_name = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
        try:
            lesson.tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))
        except:
            lesson.tutor = None

    # Подсчет статистики
    total_spent = sum([l.price for l in all_lessons if l.status == 'completed' or l.status == 'booked'])
    completed_count = all_lessons.filter(status='completed').count()
    upcoming_count = all_lessons.filter(status='booked', date__gt=timezone.now()).count()

    context = {
        'lessons': all_lessons,
        'total_spent': total_spent,
        'completed_count': completed_count,
        'upcoming_count': upcoming_count,
        'total_count': all_lessons.count()
    }

    return render(request, 'main/my_bookings.html', context)


# ========== ПРОСМОТР РЕПЕТИТОРОВ И УЧЕНИКОВ ==========

def tutors_list(request):
    # ЗАЩИТА ОТ SQL-ИНЪЕКЦИЙ: использование Django ORM
    # Все параметры автоматически экранируются
    """Список всех репетиторов"""
    tutors = User.objects.filter(role='tutor').order_by('first_name')

    # Получаем все предметы из базы
    all_subjects = Subject.objects.all()
    subjects_dict = {}
    for subject in all_subjects:
        subjects_dict[str(subject._id)] = subject.name
        subjects_dict[subject._id] = subject.name

    # Добавляем названия предметов каждому репетитору
    for tutor in tutors:
        tutor.subject_names = []
        if tutor.subject_ids:
            for subject_id in tutor.subject_ids:
                if subject_id in subjects_dict:
                    tutor.subject_names.append(subjects_dict[subject_id])
                else:
                    str_id = str(subject_id)
                    if str_id in subjects_dict:
                        tutor.subject_names.append(subjects_dict[str_id])
                    else:
                        tutor.subject_names.append(f"ID: {subject_id}")

    paginator = Paginator(tutors, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'main/tutors.html', {'page_obj': page_obj})


def students_list(request):
    """Список всех учеников"""
    students = User.objects.filter(role='student').order_by('first_name')

    # Получаем все предметы
    all_subjects = Subject.objects.all()
    subjects_dict = {}
    for subject in all_subjects:
        subjects_dict[str(subject._id)] = subject.name
        subjects_dict[subject._id] = subject.name

    # Добавляем названия предметов каждому ученику
    for student in students:
        student.subject_names = []
        if student.subject_ids:
            for subject_id in student.subject_ids:
                if subject_id in subjects_dict:
                    student.subject_names.append(subjects_dict[subject_id])
                else:
                    str_id = str(subject_id)
                    if str_id in subjects_dict:
                        student.subject_names.append(subjects_dict[str_id])
                    else:
                        student.subject_names.append(f"ID: {subject_id}")

    paginator = Paginator(students, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'main/students.html', {'page_obj': page_obj})


# ========== РАБОТА С ЗАНЯТИЯМИ ==========

@login_required
def add_lesson(request):
    """Добавление занятия (только для репетиторов)"""
    if request.user.role != 'tutor':
        messages.error(request, 'Только репетиторы могут добавлять занятия')
        return redirect('home')

    print(f"DEBUG - Current user: {request.user.email}")
    print(f"DEBUG - User role: {request.user.role}")
    print(f"DEBUG - User subject_ids: {request.user.subject_ids}")

    # Проверим, есть ли вообще предметы в базе
    all_subjects = Subject.objects.all()
    print(f"DEBUG - All subjects in DB: {[(str(s._id), s.name) for s in all_subjects]}")

    if request.method == 'POST':
        print(f"DEBUG - POST data: {request.POST}")
        form = LessonForm(request.POST, tutor=request.user)

        if form.is_valid():
            print(f"DEBUG - Form is valid: {form.cleaned_data}")

            from datetime import datetime
            lesson = Lesson(
                tutor_id=str(request.user._id),
                subject_id=form.cleaned_data['subject'],
                date=form.cleaned_data['date'],
                duration=form.cleaned_data['duration'],
                price=form.cleaned_data['price'],
                status='available'
            )
            lesson.save()
            print(f"DEBUG - Lesson saved with ID: {lesson.id}")
            messages.success(request, 'Занятие успешно добавлено!')
            return redirect('tutor_dashboard')
        else:
            print(f"DEBUG - Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = LessonForm(tutor=request.user)
        print(f"DEBUG - GET request, form created")

    return render(request, 'main/add_lesson.html', {'form': form})


@login_required
def book_lesson(request, lesson_id):
    """Запись на занятие (только для учеников)"""
    if request.user.role != 'student':
        messages.error(request, 'Только ученики могут записываться на занятия')
        return redirect('home')

    try:
        # ЗАЩИТА ОТ SQL-ИНЪЕКЦИЙ: параметр lesson_id экранируется ORM
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

        # Используем timezone.now() вместо datetime.now()
        now = timezone.now()

        print(f"DEBUG - Lesson date: {lesson.date} (type: {type(lesson.date)})")
        print(f"DEBUG - Current time: {now} (type: {type(now)})")

        # Проверки
        if lesson.status != 'available':
            messages.error(request, 'Это занятие уже недоступно')
            return redirect('available_lessons')

        if lesson.date < now:
            messages.error(request, 'Нельзя записаться на прошедшее занятие')
            return redirect('available_lessons')

        # Проверка на конфликт по времени
        conflicting = Lesson.objects.filter(
            student_id=str(request.user._id),
            status='booked',
            date=lesson.date
        ).exists()

        if conflicting:
            messages.error(request, 'У вас уже есть занятие на это время')
            return redirect('available_lessons')

        # Записываем ученика
        lesson.student_id = str(request.user._id)
        lesson.status = 'booked'
        lesson.save()

        # Удаляем из отложенных, если было
        SavedLesson.objects.filter(
            student_id=str(request.user._id),
            lesson_id=lesson_id
        ).delete()

        messages.success(request, 'Вы успешно записались на занятие!')

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')
    except Exception as e:
        messages.error(request, f'Ошибка при записи: {str(e)}')

    return redirect('student_dashboard')


def available_lessons(request):
    """Список доступных занятий"""
    from django.utils import timezone

    lessons = Lesson.objects.filter(
        status='available',
        date__gt=timezone.now()
    ).order_by('date')

    # Получаем все предметы для фильтров
    all_subjects = Subject.objects.all()

    # Получаем данные о репетиторах и предметах
    subjects_dict = {str(s._id): s.name for s in Subject.objects.all()}

    # Получаем отложенные занятия текущего ученика (если авторизован)
    saved_ids = []
    if request.user.is_authenticated and request.user.role == 'student':
        saved_ids = SavedLesson.objects.filter(
            student_id=str(request.user._id)
        ).values_list('lesson_id', flat=True)

    for lesson in lessons:
        lesson.subject_name = subjects_dict.get(str(lesson.subject_id), 'Неизвестный предмет')
        try:
            lesson.tutor = User.objects.get(_id=ObjectId(lesson.tutor_id))
        except:
            lesson.tutor = None
        lesson.is_saved = lesson.id in saved_ids

    return render(request, 'main/available_lessons.html', {
        'lessons': lessons,
        'subjects': all_subjects  # Передаем предметы в шаблон
    })


# ========== АДМИНИСТРИРОВАНИЕ (ТОЛЬКО ЧЕРЕЗ АДМИНКУ) ==========
# Все функции добавления/редактирования пользователей и предметов удалены
# Теперь это делается через стандартную админку Django

@login_required
def edit_lesson(request, lesson_id):
    """Редактирование занятия"""
    if request.user.role != 'tutor':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    try:
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

        # Проверяем, что это занятие принадлежит текущему репетитору
        if lesson.tutor_id != str(request.user._id):
            messages.error(request, 'Это не ваше занятие')
            return redirect('tutor_dashboard')

        # Проверяем, что занятие еще доступно для редактирования
        if lesson.status != 'available':
            messages.error(request, 'Нельзя редактировать занятие, на которое кто-то записан')
            return redirect('tutor_dashboard')

        if request.method == 'POST':
            form = LessonForm(request.POST, tutor=request.user)
            if form.is_valid():
                lesson.subject_id = form.cleaned_data['subject']
                lesson.date = form.cleaned_data['date']
                lesson.duration = form.cleaned_data['duration']
                lesson.price = form.cleaned_data['price']
                lesson.save()
                messages.success(request, 'Занятие успешно обновлено')
                return redirect('tutor_dashboard')
        else:
            # Предзаполняем форму данными занятия
            initial_data = {
                'subject': lesson.subject_id,
                'date': lesson.date,
                'duration': lesson.duration,
                'price': lesson.price,
            }
            form = LessonForm(initial=initial_data, tutor=request.user)

        return render(request, 'main/add_lesson.html', {'form': form, 'editing': True})

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')
        return redirect('tutor_dashboard')


@login_required
def delete_lesson(request, lesson_id):
    """Удаление занятия"""
    if request.user.role != 'tutor':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    try:
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

        if lesson.tutor_id != str(request.user._id):
            messages.error(request, 'Это не ваше занятие')
            return redirect('tutor_dashboard')

        if lesson.status != 'available':
            messages.error(request, 'Нельзя удалить занятие, на которое кто-то записан')
            return redirect('tutor_dashboard')

        lesson.delete()
        messages.success(request, 'Занятие удалено')

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')

    return redirect('tutor_dashboard')


@login_required
def complete_lesson(request, lesson_id):
    """Отметить занятие как завершенное"""
    if request.user.role != 'tutor':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    try:
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

        if lesson.tutor_id != str(request.user._id):
            messages.error(request, 'Это не ваше занятие')
            return redirect('tutor_dashboard')

        if lesson.status != 'booked':
            messages.error(request, 'Можно завершить только забронированное занятие')
            return redirect('tutor_dashboard')

        lesson.status = 'completed'
        lesson.save()
        messages.success(request, 'Занятие отмечено как завершенное')

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')

    return redirect('tutor_dashboard')


@login_required
def cancel_lesson(request, lesson_id):
    """Отмена занятия (для репетитора)"""
    if request.user.role != 'tutor':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    try:
        lesson = Lesson.objects.get(_id=ObjectId(lesson_id))

        if lesson.tutor_id != str(request.user._id):
            messages.error(request, 'Это не ваше занятие')
            return redirect('tutor_dashboard')

        if lesson.status != 'booked':
            messages.error(request, 'Можно отменить только забронированное занятие')
            return redirect('tutor_dashboard')

        lesson.status = 'cancelled'
        lesson.student_id = None
        lesson.save()
        messages.success(request, 'Занятие отменено')

    except Lesson.DoesNotExist:
        messages.error(request, 'Занятие не найдено')

    return redirect('tutor_dashboard')


def check_email(request):
    """AJAX-проверка уникальности email"""
    email = request.GET.get('email', '')

    if not email:
        return JsonResponse({'exists': False})

    # Проверяем, существует ли пользователь с таким email
    exists = User.objects.filter(email=email).exists()

    return JsonResponse({'exists': exists})

def check_phone(request):
    """AJAX-проверка уникальности телефона"""
    phone = request.GET.get('phone', '')
    if not phone:
        return JsonResponse({'exists': False})
    # Очищаем телефон от лишних символов
    cleaned = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    exists = User.objects.filter(phone=cleaned).exists()
    return JsonResponse({'exists': exists})