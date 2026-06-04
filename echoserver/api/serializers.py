from rest_framework import serializers
from main import models
from bson import ObjectId


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
        fields = ['id', 'name', 'level']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'role', 'bio', 'rating', 'subject_ids']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lesson
        fields = ['id', 'tutor_id', 'student_id', 'subject_id', 'date', 'duration', 'price', 'status']
        extra_kwargs = {
            'tutor_id': {'required': False},
            'student_id': {'required': False},
            'status': {'required': False},
        }

    def create(self, validated_data):
        # tutor_id и status уже добавлены в perform_create
        return super().create(validated_data)


class SavedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SavedLesson
        fields = ['id', 'student_id', 'lesson_id', 'added_at']


class BookingGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookingGroup
        fields = ['id', 'student_id', 'created_at', 'total_price', 'lessons_count']