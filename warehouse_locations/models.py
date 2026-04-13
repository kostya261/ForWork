from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WarehouseRack(models.Model):
    """
    Стеллаж на складе
    """
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='racks',
        verbose_name='Склад (отдел)'
    )
    name = models.CharField(max_length=100, verbose_name='Название стеллажа')
    number = models.CharField(max_length=50, unique=True, verbose_name='Номер стеллажа')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Изображения
    images = models.ManyToManyField(
        'gallery.Image',
        blank=True,
        related_name='racks',
        verbose_name='Изображения'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_racks',
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Стеллаж'
        verbose_name_plural = 'Стеллажи'
        ordering = ['department', 'number']

    def __str__(self):
        return f"{self.department.name} - {self.name} (№{self.number})"


class WarehouseCell(models.Model):
    """
    Ячейка / Место хранения
    """
    rack = models.ForeignKey(
        WarehouseRack,
        on_delete=models.CASCADE,
        related_name='cells',
        verbose_name='Стеллаж'
    )
    name = models.CharField(max_length=100, verbose_name='Название ячейки')
    number = models.CharField(max_length=50, verbose_name='Номер ячейки')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Размеры (опционально)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Ширина, см')
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Высота, см')
    depth = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Глубина, см')
    max_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     verbose_name='Макс. нагрузка, кг')

    # Изображения
    images = models.ManyToManyField(
        'gallery.Image',
        blank=True,
        related_name='cells',
        verbose_name='Изображения'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cells',
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Ячейка'
        verbose_name_plural = 'Ячейки'
        ordering = ['rack', 'number']
        unique_together = [['rack', 'number']]

    def __str__(self):
        return f"{self.rack} → {self.name} (№{self.number})"