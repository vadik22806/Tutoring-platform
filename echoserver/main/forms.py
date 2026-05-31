from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Subject, SavedLesson, BookingGroup
import re


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def validate_phone(value):
    """Валидация номера телефона"""
    if not value:
        return value

    # Убираем пробелы, дефисы, скобки
    phone = re.sub(r'[\s\-\(\)]', '', value)

    # Проверяем формат
    if not re.match(r'^\+?[0-9]{10,15}$', phone):
        raise ValidationError('Введите корректный номер телефона (10-15 цифр)')

    return phone


def validate_email_strict(value):
    """Очень строгая валидация email"""
    if not value:
        return value

    # Проверяем формат email
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
        raise ValidationError('Некорректный формат email')

    # Проверяем, что нет двух спецсимволов подряд
    local_part = value.split('@')[0]
    if re.search(r'[._-]{2,}', local_part):
        raise ValidationError('Email не может содержать два спецсимвола подряд')

    # Проверяем, что первый символ - буква или цифра
    if not local_part[0].isalnum():
        raise ValidationError('Email должен начинаться с буквы или цифры')

    # Проверяем длину (минимум 3 символа до @)
    if len(local_part) < 3:
        raise ValidationError('Слишком короткое имя пользователя')

    return value


def validate_password_length(value):
    """Проверка минимальной длины пароля"""
    if len(value) < 6:
        raise ValidationError('Пароль должен быть минимум 6 символов')
    return value


# ========== ФОРМЫ РЕГИСТРАЦИИ ==========

class StudentRegistrationForm(forms.ModelForm):
    """Форма регистрации ученика"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'}),
        label='Email',
        required=False,
        validators=[validate_email_strict]
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 999 123-45-67'}),
        label='Телефон',
        required=False,
        validators=[validate_phone]
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль',
        required=True,
        validators=[validate_password_length]
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Подтверждение пароля',
        required=True
    )

    subjects = forms.MultipleChoiceField(
        choices=[],  # Заполним в __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'subject-checkbox'}),
        required=False,
        label='Интересующие предметы'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите фамилию'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subjects = Subject.objects.all()
        self.fields['subjects'].choices = [(str(s._id), s.name) for s in subjects]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if User.objects.filter(phone=cleaned_phone).exists():
                raise ValidationError('Пользователь с таким телефоном уже существует')
            return cleaned_phone
        return phone

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')

        if not email and not phone:
            raise ValidationError('Укажите email или номер телефона')

        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError('Пароли не совпадают')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        # ЗАЩИТА ПАРОЛЯ: хеширование перед сохранением в БД
        user.set_password(self.cleaned_data['password'])

        selected_subjects = self.cleaned_data.get('subjects', [])
        user.subject_ids = list(selected_subjects)

        if commit:
            user.save()
        return user


class TutorRegistrationForm(forms.ModelForm):
    """Форма регистрации репетитора"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'}),
        label='Email',
        required=False,
        validators=[validate_email_strict]
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 999 123-45-67'}),
        label='Телефон',
        required=False,
        validators=[validate_phone]
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль',
        required=True,
        validators=[validate_password_length]
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Подтверждение пароля',
        required=True
    )

    subjects = forms.MultipleChoiceField(
        choices=[],  # Заполним в __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'subject-checkbox'}),
        required=False,
        label='Предметы для преподавания'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите фамилию'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Расскажите о себе'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subjects = Subject.objects.all()
        self.fields['subjects'].choices = [(str(s._id), s.name) for s in subjects]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if User.objects.filter(phone=cleaned_phone).exists():
                raise ValidationError('Пользователь с таким телефоном уже существует')
            return cleaned_phone
        return phone

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')

        if not email and not phone:
            raise ValidationError('Укажите email или номер телефона')

        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError('Пароли не совпадают')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'tutor'
        # ЗАЩИТА ПАРОЛЯ: хеширование перед сохранением в БД
        # Используется алгоритм pbkdf2_sha256 с солью
        user.set_password(self.cleaned_data['password'])

        selected_subjects = self.cleaned_data.get('subjects', [])
        user.subject_ids = list(selected_subjects)

        if commit:
            user.save()
        return user


# ========== ФОРМА ВХОДА ==========

class LoginForm(forms.Form):
    """Форма входа по email ИЛИ телефону"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email или номер телефона'}),
        label='Email или телефон'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
        label='Пароль'
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            from django.contrib.auth import authenticate
            # ЗАЩИТА ПАРОЛЯ: authenticate проверяет хеш, не сравнивая пароли напрямую
            user = authenticate(username=username, password=password)

            if not user:
                raise ValidationError('Неверный email/телефон или пароль')

            cleaned_data['user'] = user

        return cleaned_data


# ========== ФОРМА ДЛЯ РЕДАКТИРОВАНИЯ ПРОФИЛЯ ==========

class EditProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'}),
        label='Email',
        required=False,
        validators=[validate_email_strict]
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 999 123-45-67'}),
        label='Телефон',
        required=False,
        validators=[validate_phone]
    )

    subjects = forms.MultipleChoiceField(
        choices=[],  # Заполним в __init__
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'subject-checkbox'}),
        required=False,
        label='Интересующие предметы'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите фамилию'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'О себе'}),
        }

    def __init__(self, *args, **kwargs):
        self.user_role = kwargs.pop('user_role', None)
        super().__init__(*args, **kwargs)

        subjects = Subject.objects.all()
        self.fields['subjects'].choices = [(str(s._id), s.name) for s in subjects]

        if self.user_role == 'tutor':
            self.fields['subjects'].label = 'Предметы для преподавания'

        if self.instance and self.instance.pk and self.instance.subject_ids:
            self.fields['subjects'].initial = self.instance.subject_ids

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Пользователь с таким email уже существует')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if User.objects.filter(phone=cleaned_phone).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Пользователь с таким телефоном уже существует')
            return cleaned_phone
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)

        selected_subjects = self.cleaned_data.get('subjects', [])
        user.subject_ids = list(selected_subjects)

        if commit:
            user.save()
        return user


# ========== ФОРМЫ ДЛЯ ЗАНЯТИЙ ==========

class SubjectSelectionForm(forms.Form):
    """Форма для выбора предметов (для создания занятия)"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        subjects = Subject.objects.all().order_by('name')

        for subject in subjects:
            field_name = f"subject_{subject.id}"
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=subject.name,
                widget=forms.CheckboxInput(attrs={'class': 'subject-checkbox form-check-input'})
            )

    def get_selected_subjects(self):
        selected = []
        for field_name, value in self.cleaned_data.items():
            if value and field_name.startswith('subject_'):
                subject_id = field_name.replace('subject_', '')
                selected.append(subject_id)
        return selected


class LessonForm(forms.Form):
    """Форма для создания занятия (для репетиторов)"""

    subject = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Предмет',
        required=True
    )
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Дата и время',
        required=True
    )
    duration = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '60'}),
        label='Длительность (минуты)',
        min_value=15,
        required=True
    )
    price = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1000'}),
        label='Цена (руб)',
        min_value=0,
        required=True
    )

    def __init__(self, *args, **kwargs):
        self.tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)

        from bson import ObjectId

        if self.tutor and self.tutor.subject_ids:
            subject_oids = []
            for sid in self.tutor.subject_ids:
                try:
                    subject_oids.append(ObjectId(sid))
                except Exception:
                    pass

            subjects = Subject.objects.filter(_id__in=subject_oids)
            choices = [(str(s._id), s.name) for s in subjects]
        else:
            subjects = Subject.objects.all()
            choices = [(str(s._id), s.name) for s in subjects]

        if not choices:
            choices = [('', '--- Нет доступных предметов ---')]

        self.fields['subject'].choices = choices

    def clean_date(self):
        date = self.cleaned_data.get('date')
        from django.utils import timezone

        now = timezone.now()

        if date < now:
            raise ValidationError('Нельзя создать занятие в прошлом')
        return date