from django.db import models


class Position(models.Model):
    """
    Должность сотрудника (Электрик, Монтажник, Дворник и т.д.)
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['name']

    def __str__(self):
        return self.name