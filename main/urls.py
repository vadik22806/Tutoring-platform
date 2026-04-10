from django.urls import path
from . import views

urlpatterns = [
    # ========== ОСНОВНЫЕ СТРАНИЦЫ ==========
    path('', views.home, name='home'),
    path('about', views.about, name='about'),

    # ========== АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ==========
    path('login/choice/', views.login_choice, name='login_choice'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/choice/', views.register_choice, name='register_choice'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/tutor/', views.register_tutor, name='register_tutor'),

    # ========== ЛИЧНЫЕ КАБИНЕТЫ ==========
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/tutor/', views.tutor_dashboard, name='tutor_dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # ========== ПРОСМОТР ПОЛЬЗОВАТЕЛЕЙ ==========
    path('tutors/', views.tutors_list, name='tutors_list'),
    path('students/', views.students_list, name='students_list'),

    # ========== РАБОТА С ЗАНЯТИЯМИ ==========
    path('lessons/available/', views.available_lessons, name='available_lessons'),
    path('lessons/add/', views.add_lesson, name='add_lesson'),
    path('lessons/<str:lesson_id>/book/', views.book_lesson, name='book_lesson'),

    # ========== УПРАВЛЕНИЕ ЗАНЯТИЯМИ ==========
    path('lessons/<str:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('lessons/<str:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    path('lessons/<str:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('lessons/<str:lesson_id>/cancel/', views.cancel_lesson, name='cancel_lesson'),

    # ========== ОТЛОЖЕННЫЕ ЗАНЯТИЯ (КОРЗИНА) ==========
    path('lessons/<str:lesson_id>/save/', views.save_lesson, name='save_lesson'),
    path('lessons/<str:lesson_id>/unsave/', views.unsave_lesson, name='unsave_lesson'),
    path('saved-lessons/', views.saved_lessons, name='saved_lessons'),
    path('saved-lessons/book-all/', views.book_all_saved, name='book_all_saved'),

    # ========== ИСТОРИЯ ЗАПИСЕЙ ==========
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # ========== AJAX ДЛЯ ВАЛИДАЦИИ ==========
    path('check-email/', views.check_email, name='check_email'),
    path('check-phone/', views.check_phone, name='check_phone'),# НОВЫЙ МАРШРУТ
]