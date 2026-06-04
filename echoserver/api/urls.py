from django.urls import path
from .views import (
    PingView, SubjectListView,
    RegisterView, LoginView, LogoutView, MeView,
    TutorListView, StudentListView, UserDetailView, UserUpdateView,
    AvailableLessonsView, LessonListCreateView,
    LessonDetailView, CompleteLessonView, CancelLessonView,
    BookLessonView, CancelBookingView, MyBookingsView,
    SavedLessonListView, SaveLessonView, UnsaveLessonView, BookAllSavedView,
    DashboardView, CheckEmailView, CheckPhoneView,
    DebugAuthView
)

urlpatterns = [
    # Проверка
    path('ping/', PingView.as_view(), name='api-ping'),

    # Авторизация
    path('auth/register/', RegisterView.as_view(), name='api-auth-register'),
    path('auth/login/', LoginView.as_view(), name='api-auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='api-auth-logout'),
    path('auth/me/', MeView.as_view(), name='api-auth-me'),
    path('auth/debug/', DebugAuthView.as_view(), name='api-auth-debug'),

    # Пользователи
    path('users/tutors/', TutorListView.as_view(), name='api-users-tutors'),
    path('users/students/', StudentListView.as_view(), name='api-users-students'),
    path('users/<str:id>/', UserDetailView.as_view(), name='api-user-detail'),
    path('users/<str:id>/update/', UserUpdateView.as_view(), name='api-user-update'),

    # Дашборды
    path('users/me/dashboard/', DashboardView.as_view(), name='api-my-dashboard'),

    # Занятия
    path('lessons/available/', AvailableLessonsView.as_view(), name='api-lessons-available'),
    path('lessons/', LessonListCreateView.as_view(), name='api-lessons-list'),
    path('lessons/<str:id>/', LessonDetailView.as_view(), name='api-lesson-detail'),
    path('lessons/<str:id>/complete/', CompleteLessonView.as_view(), name='api-lesson-complete'),
    path('lessons/<str:id>/cancel/', CancelLessonView.as_view(), name='api-lesson-cancel'),

    # Записи (bookings)
    path('bookings/', BookLessonView.as_view(), name='api-book-lesson'),
    path('bookings/<str:id>/cancel/', CancelBookingView.as_view(), name='api-cancel-booking'),
    path('bookings/me/', MyBookingsView.as_view(), name='api-my-bookings'),

    # Избранное (saved)
    path('saved/', SavedLessonListView.as_view(), name='api-saved-list'),
    path('saved/<str:id>/save/', SaveLessonView.as_view(), name='api-save-lesson'),
    path('saved/<str:id>/unsave/', UnsaveLessonView.as_view(), name='api-unsave-lesson'),
    path('saved/book-all/', BookAllSavedView.as_view(), name='api-book-all-saved'),

    # Предметы
    path('subjects/', SubjectListView.as_view(), name='api-subjects'),

    # AJAX проверки
    path('check-email/', CheckEmailView.as_view(), name='api-check-email'),
    path('check-phone/', CheckPhoneView.as_view(), name='api-check-phone'),
]
