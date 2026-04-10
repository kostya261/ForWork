from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class InventoryCategory(MPTTModel):
    """
    Иерархическая структура категорий для инвентаря (основных средств).
    Пример: Инструмент → Электроинструмент → Дрели → Аккумуляторные
    """
    name = models.CharField(max_length=100, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительская категория'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Категория инвентаря'
        verbose_name_plural = 'Категории инвентаря'

    def __str__(self):
        return self.name