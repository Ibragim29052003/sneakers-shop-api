"""
модели приложения пользователей
"""
from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class UserManager(BaseUserManager):
    # менеджер для кастомной модели пользователя
    def create_user(self, email: Any, password: Any=None, **extra_fields: Any) -> Any:
        # создание и сохранение обычного пользователя
        """Выполняет действие `create_user`."""
        if not email:
            raise ValueError('поле email должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email: Any, password: Any=None, **extra_fields: Any) -> Any:
        # создание и сохранение суперпользователя
        """Выполняет действие `create_superuser`."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # кастомная модель пользователя с email в качестве основного идентификатора
    username = None  # удаляем поле username
    email = models.EmailField('email адрес', unique=True)
    is_active = models.BooleanField('активен', default=True)
    date_joined = models.DateTimeField('дата регистрации', default=timezone.now)
    
    # отслеживание истории изменений через simple_history
    history = HistoricalRecords()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
    
    def __str__(self) -> Any:
        """Выполняет действие `__str__`."""
        return self.email


class Role(models.Model):
    # модель ролей пользователей
    name = models.CharField('название роли', max_length=50, unique=True)
    description = models.TextField('описание', blank=True)
    
    class Meta:
        verbose_name = 'роль'
        verbose_name_plural = 'роли'
    
    def __str__(self) -> Any:
        """Выполняет действие `__str__`."""
        return self.name


class UserRole(models.Model):
    # связь пользователей и ролей (многие-ко-многим)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_roles',
        verbose_name='пользователь'
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE, 
        related_name='role_users',
        verbose_name='роль'
    )
    assigned_at = models.DateTimeField('дата назначения', default=timezone.now)
    
    class Meta:
        unique_together = ('user', 'role')
        verbose_name = 'назначение роли'
        verbose_name_plural = 'назначения ролей'
    
    def __str__(self) -> Any:
        """Выполняет действие `__str__`."""
        return f'{self.user.email} - {self.role.name}'


class UserProfile(models.Model):
    # дополнительная информация о пользователе
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='пользователь'
    )
    phone = models.CharField('телефон', max_length=20, blank=True)
    address = models.CharField('адрес', max_length=255, blank=True)
    city = models.CharField('город', max_length=100, blank=True)
    postal_code = models.CharField('почтовый индекс', max_length=20, blank=True)
    country = models.CharField('страна', max_length=100, blank=True)
    created_at = models.DateTimeField('дата создания', default=timezone.now)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'профиль пользователя'
        verbose_name_plural = 'профили пользователей'
    
    def __str__(self) -> Any:
        """Выполняет действие `__str__`."""
        return f'профиль пользователя {self.user.email}'
