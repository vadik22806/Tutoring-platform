from rest_framework import serializers
from main import models


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
        fields = ['id', 'name', 'level']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'role', 'bio', 'rating', 'subject_ids']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lesson
        fields = ['id', 'tutor_id', 'student_id', 'subject_id', 'date', 'duration', 'price', 'status']


class SavedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SavedLesson
        fields = ['id', 'student_id', 'lesson_id', 'added_at']


class BookingGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookingGroup
        fields = ['id', 'student_id', 'created_at', 'total_price', 'lessons_count']
