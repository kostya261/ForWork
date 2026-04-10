from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    """
    # Основная информация
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='Отчество')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(unique=True, verbose_name='Email')  # Делаем email уникальным

    # Мессенджеры
    telegram = models.CharField(max_length=100, blank=True, verbose_name='Telegram')
    whatsapp = models.CharField(max_length=100, blank=True, verbose_name='WhatsApp')

    # Паспортные данные
    passport_series = models.CharField(max_length=4, blank=True, verbose_name='Серия паспорта')
    passport_number = models.CharField(max_length=6, blank=True, verbose_name='Номер паспорта')
    passport_issued_by = models.TextField(blank=True, verbose_name='Кем выдан')
    passport_issued_date = models.DateField(null=True, blank=True, verbose_name='Дата выдачи')

    # Связи
    position = models.ForeignKey(
        'positions.Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Должность'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Отдел'
    )

    # Транспорт и прочее
    has_transport = models.BooleanField(default=False, verbose_name='Наличие транспорта')
    transport_description = models.CharField(max_length=200, blank=True, verbose_name='Описание транспорта')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    # Фото (пока без связи с Gallery, добавим позже)
    photo = models.ForeignKey('gallery.Image', on_delete=models.SET_NULL, null=True, blank=True)

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return self.get_full_name() or self.username

    def get_full_name(self):
        """Возвращает ФИО полностью"""
        full_name = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return full_name if full_name else self.username