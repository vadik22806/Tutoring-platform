from django.contrib import admin
from .models import User, Subject, Lesson
from django import forms


class SubjectAdminForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = '__all__'

    # Преобразуем строку в JSON
    level = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '["school", "university"]'}),
        help_text='Введите в формате: ["school", "university"] или ["school"]'
    )

    def clean_level(self):
        data = self.cleaned_data['level']
        if isinstance(data, str):
            try:
                # Пробуем распарсить как JSON
                import json
                return json.loads(data)
            except:
                # Если не JSON, делаем список из одного элемента
                return [data]
        return data


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    form = SubjectAdminForm
    list_display = ['id', 'name', 'level']
    search_fields = ['name']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = ['role', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    fieldsets = (
        ('Основное', {
            'fields': ('email', 'first_name', 'last_name', 'role')
        }),
        ('Контакты', {
            'fields': ('phone',)
        }),
        ('Предметы и рейтинг', {
            'fields': ('subject_ids', 'rating', 'bio')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject_id', 'date', 'status']
    list_filter = ['status']
    search_fields = ['tutor_id', 'student_id']