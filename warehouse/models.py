from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WarehouseItem(models.Model):
    """
    Расходные материалы на складе.
    """
    UNIT_CHOICES = (
        ('pcs', 'шт.'),
        ('kg', 'кг'),
        ('m', 'м'),
        ('l', 'л'),
        ('pack', 'упак.'),
        ('set', 'компл.'),
    )

    # Основная информация
    name = models.CharField(max_length=200, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')
    article = models.CharField(max_length=50, blank=True, verbose_name='Артикул')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='Серийный номер')

    # Категория (иерархическая)
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_items',
        verbose_name='Категория'
    )

    # Производитель
    manufacturer = models.ForeignKey(
        'manufacturers.Manufacturer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_items',
        verbose_name='Производитель'
    )

    # Количество и единицы измерения
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name='Количество')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs', verbose_name='Ед. изм.')
    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name='Мин. остаток')

    # Цены
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                         verbose_name='Цена закупочная')
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                       verbose_name='Цена розничная')

    # Принадлежность
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_items',
        verbose_name='Отдел'
    )

    # Ячейка на складе
    cell = models.ForeignKey(
        'warehouse_locations.WarehouseCell',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        verbose_name='Место хранения (ячейка)'
    )

    # Изображения
    images = models.ManyToManyField(
        'gallery.Image',
        blank=True,
        related_name='warehouse_items',
        verbose_name='Изображения'
    )

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Складская позиция'
        verbose_name_plural = 'Складские позиции'
        ordering = ['name']

    def get_first_image(self):
        """Возвращает первое изображение или None"""
        return self.images.first()

    def get_image_url(self):
        """URL первого изображения или заглушка"""
        img = self.get_first_image()
        if img and img.image:
            return img.image.url
        return None

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.get_unit_display()})"

    @property
    def is_low_stock(self):
        """Проверка на минимальный остаток"""
        return self.quantity <= self.min_stock


class WarehouseTransaction(models.Model):
    """
    Журнал движения расходников (поступление, списание, перемещение).
    """
    TRANSACTION_TYPES = (
        ('in', 'Поступление'),
        ('out', 'Списание'),
        ('move', 'Перемещение между отделами'),
        ('reserve', 'Резервирование под задачу'),
        ('return', 'Возврат'),
    )

    item = models.ForeignKey(
        WarehouseItem,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Товар'
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name='Тип операции')
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Количество')

    # Откуда и куда
    from_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_transactions',
        verbose_name='Отдел-отправитель'
    )
    to_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transactions',
        verbose_name='Отдел-получатель'
    )

    # Связь с задачей (если списание под задачу)
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_transactions',
        verbose_name='Задача'
    )

    # Комментарий и кто провел операцию
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='warehouse_transactions',
        verbose_name='Провел операцию'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата операции')

    class Meta:
        verbose_name = 'Операция по складу'
        verbose_name_plural = 'Журнал операций по складу'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.item.name} ({self.quantity})"
