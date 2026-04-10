from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class InventoryItem(models.Model):
    """
    Основные средства (инвентарь) — оборудование многократного использования.
    """
    STATUS_CHOICES = (
        ('active', 'Активен'),
        ('repair', 'В ремонте'),
        ('decommissioned', 'Списан'),
        ('lost', 'Утерян'),
    )

    # Основная информация
    name = models.CharField(max_length=200, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')
    manufacturer = models.ForeignKey(
        'manufacturers.Manufacturer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name='Производитель'
    )

    # Учетные номера
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='Серийный номер')
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name='Инвентарный номер')

    # Даты
    production_date = models.DateField(null=True, blank=True, verbose_name='Дата производства')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='Дата приобретения')
    receipt_date = models.DateField(null=True, blank=True, verbose_name='Дата поступления на склад')
    decommission_date = models.DateField(null=True, blank=True, verbose_name='Дата списания')

    # Стоимость
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                         verbose_name='Цена закупочная')

    # Статус и причина списания
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    decommission_reason = models.TextField(blank=True, verbose_name='Причина списания')

    # Связи
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name='Отдел'
    )
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_inventory',
        verbose_name='Ответственный'
    )

    # Изображения
    images = models.ManyToManyField(
        'gallery.Image',
        blank=True,
        related_name='inventory_items',
        verbose_name='Изображения'
    )

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    category = models.ForeignKey(
        'inventory_categories.InventoryCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name='Категория'
    )

    class Meta:
        verbose_name = 'Инвентарь'
        verbose_name_plural = 'Инвентарь'
        ordering = ['-created_at']

    def get_category_path(self):
        if self.category:
            ancestors = self.category.get_ancestors(include_self=True)
            return ' / '.join(a.name for a in ancestors)
        return '—'

    def get_first_image(self):
        """Возвращает первое изображение или None"""
        return self.images.first()

    def get_image_url(self):
        """URL первого изображения или заглушка"""
        img = self.get_first_image()
        if img and img.image:
            return img.image.url
        return '/static/img/no-image.png'

    def __str__(self):
        return f"{self.name} (Инв. №{self.inventory_number})"