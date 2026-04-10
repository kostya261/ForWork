from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class MaterialRequest(models.Model):
    """
    Требование-накладная на получение материалов со склада.
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('pending', 'Ожидает одобрения'),
        ('approved', 'Одобрено'),
        ('issued', 'Выдано'),
        ('partially_issued', 'Частично выдано'),
        ('closed', 'Закрыто'),
        ('cancelled', 'Отменено'),
    )

    # Номер документа (автоматически генерируем)
    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    # Связи
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='material_requests',
        verbose_name='Задача'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='material_requests',
        verbose_name='Отдел-получатель'
    )

    # Статус и даты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    requested_date = models.DateField(verbose_name='Дата требования')
    issued_date = models.DateField(null=True, blank=True, verbose_name='Дата выдачи')

    # Кто участвовал
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_material_requests',
        verbose_name='Создал'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_material_requests',
        verbose_name='Одобрил'
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_material_requests',
        verbose_name='Выдал'
    )

    # Комментарий
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Требование-накладная'
        verbose_name_plural = 'Требования-накладные'
        ordering = ['-created_at']
        permissions = [
            ('can_approve_materialrequest', 'Может одобрять требования'),
            ('can_issue_materialrequest', 'Может выдавать материалы'),
        ]

    def __str__(self):
        return f"Требование №{self.number} от {self.requested_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            # Генерируем номер: ТР-20260410-001
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = MaterialRequest.objects.filter(number__startswith=f'ТР-{date_str}').count()
            self.number = f'ТР-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class MaterialRequestItem(models.Model):
    """
    Строка требования-накладной.
    """
    request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Требование'
    )
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.PROTECT,
        related_name='material_request_items',
        verbose_name='Материал'
    )
    requested_quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(0.001)],
        verbose_name='Запрошено'
    )
    issued_quantity = models.DecimalField(
        max_digits=10, decimal_places=3,
        default=0,
        verbose_name='Выдано'
    )
    comment = models.CharField(max_length=200, blank=True, verbose_name='Примечание')

    class Meta:
        verbose_name = 'Строка требования'
        verbose_name_plural = 'Строки требования'
        unique_together = ['request', 'warehouse_item']

    def __str__(self):
        return f"{self.warehouse_item.name}: {self.requested_quantity}"


class InventoryIssue(models.Model):
    """
    Накладная на выдачу инвентаря (основных средств).
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('pending', 'Ожидает одобрения'),
        ('approved', 'Одобрено'),
        ('issued', 'Выдано'),
        ('returned', 'Возвращено'),
        ('closed', 'Закрыто'),
        ('cancelled', 'Отменено'),
    )

    # Номер документа
    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    # Связи
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_issues',
        verbose_name='Задача'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='inventory_issues',
        verbose_name='Отдел-получатель'
    )

    # Статус и даты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    issue_date = models.DateField(verbose_name='Дата выдачи')
    return_date = models.DateField(null=True, blank=True, verbose_name='Дата возврата')

    # Кто участвовал
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_inventory_issues',
        verbose_name='Создал'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_inventory_issues',
        verbose_name='Одобрил'
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_inventory_issues',
        verbose_name='Выдал'
    )

    # Комментарий
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Накладная на инвентарь'
        verbose_name_plural = 'Накладные на инвентарь'
        ordering = ['-created_at']
        permissions = [
            ('can_approve_inventoryissue', 'Может одобрять выдачу инвентаря'),
            ('can_issue_inventoryissue', 'Может выдавать инвентарь'),
        ]

    def __str__(self):
        return f"Накладная №{self.number} от {self.issue_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = InventoryIssue.objects.filter(number__startswith=f'ИН-{date_str}').count()
            self.number = f'ИН-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class InventoryIssueItem(models.Model):
    """
    Строка накладной на инвентарь.
    """
    issue = models.ForeignKey(
        InventoryIssue,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Накладная'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='issue_items',
        verbose_name='Инвентарь'
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Количество')
    responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='responsible_inventory_issues',
        verbose_name='Ответственный'
    )
    returned = models.BooleanField(default=False, verbose_name='Возвращено')
    comment = models.CharField(max_length=200, blank=True, verbose_name='Примечание')

    class Meta:
        verbose_name = 'Строка накладной'
        verbose_name_plural = 'Строки накладной'

    def __str__(self):
        return f"{self.inventory_item.name} ({self.quantity} шт.) → {self.responsible.get_full_name()}"