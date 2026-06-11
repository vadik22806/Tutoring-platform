"""
Кастомные permission-классы для API.

Заменяют ad-hoc проверки ролей в views.py
на декларативные permission-классы DRF.
"""
from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """Разрешение только для учеников"""
    message = 'Только ученики могут выполнять это действие'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'student')


class IsTutor(BasePermission):
    """Разрешение только для репетиторов"""
    message = 'Только репетиторы могут выполнять это действие'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'tutor')


class IsAdmin(BasePermission):
    """Разрешение только для администраторов"""
    message = 'Только администраторы могут выполнять это действие'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsOwnerOrAdmin(BasePermission):
    """
    Разрешение: пользователь является владельцем объекта (user_id совпадает)
    или администратором. Используется для редактирования профиля и т.д.
    """
    message = 'Вы можете редактировать только свой профиль'

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        # Проверяем по _id или по полю tutor_id/student_id
        obj_id = str(getattr(obj, '_id', ''))
        return obj_id == str(request.user._id)

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsTutorOrAdmin(BasePermission):
    """Разрешение для репетитора-владельца занятия или админа"""
    message = 'Это не ваше занятие'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsLessonOwner(BasePermission):
    """
    Разрешение: пользователь является владельцем занятия (tutor_id совпадает)
    или администратором.
    """
    message = 'Это не ваше занятие'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return str(obj.tutor_id) == str(request.user._id)


class IsBookingOwner(BasePermission):
    """
    Разрешение: пользователь является владельцем записи (student_id совпадает)
    или администратором.
    """
    message = 'Это не ваша запись'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return str(obj.student_id) == str(request.user._id)