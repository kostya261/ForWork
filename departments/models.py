from django.db import models


class Department(models.Model):
    """
    Отдел / Структурное подразделение
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Адреса
    legal_address = models.TextField(blank=True, verbose_name='Юридический адрес')
    actual_address = models.TextField(blank=True, verbose_name='Фактический адрес')

    # Иерархия
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительский отдел'
    )

    # Руководитель отдела
    head = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        verbose_name='Руководитель отдела'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name