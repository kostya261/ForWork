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


class WarehouseReceipt(models.Model):
    """
    Приходная накладная (поступление товаров на склад)
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведён'),
        ('cancelled', 'Отменён'),
    )

    # Номер документа (автоматически генерируем)
    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    # Поставщик
    supplier = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.PROTECT,
        related_name='warehouse_receipts',
        verbose_name='Поставщик'
    )

    # Склад (отдел-получатель)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='warehouse_receipts',
        verbose_name='Склад'
    )

    # Статус и даты
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    receipt_date = models.DateField(verbose_name='Дата поступления')

    # Кто создал / провёл
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_receipts',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_receipts',
        verbose_name='Провёл'
    )

    # Комментарий
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Приходная накладная'
        verbose_name_plural = 'Приходные накладные'
        ordering = ['-created_at']

    def __str__(self):
        return f"Приходная накладная №{self.number} от {self.receipt_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = WarehouseReceipt.objects.filter(number__startswith=f'ПР-{date_str}').count()
            self.number = f'ПР-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)

    @property
    def total_sum(self):
        return sum(item.total for item in self.items.all())


class WarehouseReceiptItem(models.Model):
    """
    Строка приходной накладной
    """
    receipt = models.ForeignKey(
        WarehouseReceipt,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Накладная'
    )
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.PROTECT,
        related_name='receipt_items',
        verbose_name='Товар'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Количество')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'Строка приходной накладной'
        verbose_name_plural = 'Строки приходной накладной'

    def __str__(self):
        return f"{self.warehouse_item.name} x {self.quantity}"

    @property
    def total(self):
        return self.quantity * self.price


class WarehouseExpense(models.Model):
    """
    Расходная накладная (списание товаров со склада)
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведён'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='warehouse_expenses',
        verbose_name='Склад (отдел)'
    )

    # Для кого списываем (необязательно)
    counterparty = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_expenses',
        verbose_name='Получатель'
    )

    # Связь с задачей (если списание под задачу)
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_expenses',
        verbose_name='Задача'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    expense_date = models.DateField(verbose_name='Дата списания')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_expenses',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_expenses',
        verbose_name='Провёл'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Расходная накладная'
        verbose_name_plural = 'Расходные накладные'
        ordering = ['-created_at']

    def __str__(self):
        return f"Расходная накладная №{self.number} от {self.expense_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = WarehouseExpense.objects.filter(number__startswith=f'РН-{date_str}').count()
            self.number = f'РН-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)

    @property
    def total_sum(self):
        return sum(item.total for item in self.items.all())


class WarehouseExpenseItem(models.Model):
    """
    Строка расходной накладной
    """
    expense = models.ForeignKey(
        WarehouseExpense,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Накладная'
    )
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.PROTECT,
        related_name='expense_items',
        verbose_name='Товар'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Количество')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'Строка расходной накладной'
        verbose_name_plural = 'Строки расходной накладной'

    def __str__(self):
        return f"{self.warehouse_item.name} x {self.quantity}"

    @property
    def total(self):
        return self.quantity * self.price


class WarehouseTransfer(models.Model):
    """
    Перемещение товаров между складами (отделами)
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведён'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    from_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='outgoing_transfers',
        verbose_name='Склад-отправитель'
    )
    to_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='incoming_transfers',
        verbose_name='Склад-получатель'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    transfer_date = models.DateField(verbose_name='Дата перемещения')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_transfers',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_transfers',
        verbose_name='Провёл'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Перемещение товаров'
        verbose_name_plural = 'Перемещения товаров'
        ordering = ['-created_at']

    def __str__(self):
        return f"Перемещение №{self.number} от {self.transfer_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = WarehouseTransfer.objects.filter(number__startswith=f'ПМ-{date_str}').count()
            self.number = f'ПМ-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class WarehouseTransferItem(models.Model):
    """
    Строка перемещения
    """
    transfer = models.ForeignKey(
        WarehouseTransfer,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Перемещение'
    )
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.PROTECT,
        related_name='transfer_items',
        verbose_name='Товар'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Количество')

    class Meta:
        verbose_name = 'Строка перемещения'
        verbose_name_plural = 'Строки перемещения'

    def __str__(self):
        return f"{self.warehouse_item.name} x {self.quantity}"


class WarehouseStocktake(models.Model):
    """
    Инвентаризация склада (сверка остатков)
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведена'),
        ('cancelled', 'Отменена'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='stocktakes',
        verbose_name='Склад'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    stocktake_date = models.DateField(verbose_name='Дата инвентаризации')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_stocktakes',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_stocktakes',
        verbose_name='Провёл'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Инвентаризация'
        verbose_name_plural = 'Инвентаризации'
        ordering = ['-created_at']

    def __str__(self):
        return f"Инвентаризация №{self.number} от {self.stocktake_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = WarehouseStocktake.objects.filter(number__startswith=f'ИНВ-{date_str}').count()
            self.number = f'ИНВ-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class WarehouseStocktakeItem(models.Model):
    """
    Строка инвентаризации
    """
    stocktake = models.ForeignKey(
        WarehouseStocktake,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Инвентаризация'
    )
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.PROTECT,
        related_name='stocktake_items',
        verbose_name='Товар'
    )
    book_quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Учётное количество')
    actual_quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Фактическое количество')

    class Meta:
        verbose_name = 'Строка инвентаризации'
        verbose_name_plural = 'Строки инвентаризации'

    def __str__(self):
        return f"{self.warehouse_item.name}: {self.book_quantity} → {self.actual_quantity}"

    @property
    def difference(self):
        return self.actual_quantity - self.book_quantity


class InventoryWriteOff(models.Model):
    """
    Списание основных средств
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведён'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='inventory_writeoffs',
        verbose_name='Отдел'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    writeoff_date = models.DateField(verbose_name='Дата списания')
    reason = models.TextField(verbose_name='Причина списания')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_writeoffs',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_writeoffs',
        verbose_name='Провёл'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Списание ОС'
        verbose_name_plural = 'Списания ОС'
        ordering = ['-created_at']

    def __str__(self):
        return f"Списание №{self.number} от {self.writeoff_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = InventoryWriteOff.objects.filter(number__startswith=f'СП-{date_str}').count()
            self.number = f'СП-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class InventoryWriteOffItem(models.Model):
    """
    Строка списания ОС
    """
    writeoff = models.ForeignKey(
        InventoryWriteOff,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Списание'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='writeoff_items',
        verbose_name='Инвентарь'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Строка списания ОС'
        verbose_name_plural = 'Строки списания ОС'

    def __str__(self):
        return f"{self.inventory_item.name} x {self.quantity}"


class InventoryTransfer(models.Model):
    """
    Перемещение основных средств
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведён'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    from_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='outgoing_inventory_transfers',
        verbose_name='Отдел-отправитель'
    )
    to_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='incoming_inventory_transfers',
        verbose_name='Отдел-получатель'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    transfer_date = models.DateField(verbose_name='Дата перемещения')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_inventory_transfers',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_inventory_transfers',
        verbose_name='Провёл'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Перемещение ОС'
        verbose_name_plural = 'Перемещения ОС'
        ordering = ['-created_at']

    def __str__(self):
        return f"Перемещение ОС №{self.number} от {self.transfer_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = InventoryTransfer.objects.filter(number__startswith=f'ПОС-{date_str}').count()
            self.number = f'ПОС-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class InventoryTransferItem(models.Model):
    """
    Строка перемещения ОС
    """
    transfer = models.ForeignKey(
        InventoryTransfer,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Перемещение'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='transfer_items',
        verbose_name='Инвентарь'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    new_responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='received_inventory',
        verbose_name='Новый ответственный'
    )

    class Meta:
        verbose_name = 'Строка перемещения ОС'
        verbose_name_plural = 'Строки перемещения ОС'

    def __str__(self):
        return f"{self.inventory_item.name} → {self.new_responsible.get_full_name()}"


class InventoryStocktake(models.Model):
    """
    Инвентаризация основных средств
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('conducted', 'Проведена'),
        ('cancelled', 'Отменена'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='inventory_stocktakes',
        verbose_name='Отдел'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    stocktake_date = models.DateField(verbose_name='Дата инвентаризации')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_inventory_stocktakes',
        verbose_name='Создал'
    )
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_inventory_stocktakes',
        verbose_name='Провёл'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Инвентаризация ОС'
        verbose_name_plural = 'Инвентаризации ОС'
        ordering = ['-created_at']

    def __str__(self):
        return f"Инвентаризация ОС №{self.number} от {self.stocktake_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = InventoryStocktake.objects.filter(number__startswith=f'ИНВОС-{date_str}').count()
            self.number = f'ИНВОС-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class InventoryStocktakeItem(models.Model):
    """
    Строка инвентаризации ОС
    """
    stocktake = models.ForeignKey(
        InventoryStocktake,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Инвентаризация'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='stocktake_items',
        verbose_name='Инвентарь'
    )
    book_quantity = models.PositiveIntegerField(default=1, verbose_name='Учётное количество')
    actual_quantity = models.PositiveIntegerField(default=0, verbose_name='Фактическое количество')

    class Meta:
        verbose_name = 'Строка инвентаризации ОС'
        verbose_name_plural = 'Строки инвентаризации ОС'

    def __str__(self):
        return f"{self.inventory_item.name}: {self.book_quantity} → {self.actual_quantity}"

    @property
    def difference(self):
        return self.actual_quantity - self.book_quantity


class WorkOrder(models.Model):
    """
    Наряд на выполнение работ
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('issued', 'Выдан'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер наряда')

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.PROTECT,
        related_name='work_orders',
        verbose_name='Задача'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    issue_date = models.DateField(verbose_name='Дата выдачи')
    planned_completion_date = models.DateField(null=True, blank=True, verbose_name='Плановое завершение')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_work_orders',
        verbose_name='Создал'
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_work_orders',
        verbose_name='Выдал'
    )

    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_work_orders',
        verbose_name='Ответственный'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Наряд на работу'
        verbose_name_plural = 'Наряды на работу'
        ordering = ['-created_at']

    def __str__(self):
        return f"Наряд №{self.number} к задаче #{self.task.pk}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = WorkOrder.objects.filter(number__startswith=f'НР-{date_str}').count()
            self.number = f'НР-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class WorkOrderMaterial(models.Model):
    """Материалы по наряду"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='materials')
    warehouse_item = models.ForeignKey('warehouse.WarehouseItem', on_delete=models.PROTECT)
    planned_quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Плановое количество')

    class Meta:
        verbose_name = 'Материал наряда'
        verbose_name_plural = 'Материалы наряда'


class WorkOrderInventory(models.Model):
    """Инвентарь по наряду"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='inventory')
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Инвентарь наряда'
        verbose_name_plural = 'Инвентарь наряда'


class CompletionAct(models.Model):
    """
    Акт выполненных работ
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('signed', 'Подписан'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер акта')

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.PROTECT,
        related_name='completion_acts',
        verbose_name='Задача'
    )
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completion_acts',
        verbose_name='Наряд'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    completion_date = models.DateField(verbose_name='Дата выполнения')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_acts',
        verbose_name='Создал'
    )
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_acts',
        verbose_name='Подписал'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Акт выполненных работ'
        verbose_name_plural = 'Акты выполненных работ'
        ordering = ['-created_at']

    def __str__(self):
        return f"Акт №{self.number} к задаче #{self.task.pk}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = CompletionAct.objects.filter(number__startswith=f'АВР-{date_str}').count()
            self.number = f'АВР-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)


class CompletionActMaterial(models.Model):
    """Фактически потраченные материалы"""
    act = models.ForeignKey(CompletionAct, on_delete=models.CASCADE, related_name='materials')
    warehouse_item = models.ForeignKey('warehouse.WarehouseItem', on_delete=models.PROTECT)
    actual_quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Фактическое количество')

    class Meta:
        verbose_name = 'Материал акта'
        verbose_name_plural = 'Материалы акта'


class Invoice(models.Model):
    """
    Счёт на оплату
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('sent', 'Отправлен'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер счёта')

    counterparty = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='Контрагент'
    )

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='Задача'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    invoice_date = models.DateField(verbose_name='Дата счёта')
    due_date = models.DateField(null=True, blank=True, verbose_name='Оплатить до')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_invoices',
        verbose_name='Создал'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Счёт на оплату'
        verbose_name_plural = 'Счета на оплату'
        ordering = ['-created_at']

    def __str__(self):
        return f"Счёт №{self.number} от {self.invoice_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = Invoice.objects.filter(number__startswith=f'СЧ-{date_str}').count()
            self.number = f'СЧ-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)

    @property
    def total_sum(self):
        return sum(item.total for item in self.items.all())


class InvoiceItem(models.Model):
    """
    Строка счёта на оплату
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Счёт'
    )

    # Можно выбрать товар со склада ИЛИ вписать вручную
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items',
        verbose_name='Товар со склада'
    )
    description = models.CharField(max_length=200, blank=True, verbose_name='Описание')

    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Количество')
    unit = models.CharField(max_length=20, default='шт', verbose_name='Ед. изм.')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'Строка счёта'
        verbose_name_plural = 'Строки счёта'

    def __str__(self):
        desc = self.warehouse_item.name if self.warehouse_item else self.description
        return f"{desc} x {self.quantity}"

    @property
    def total(self):
        return self.quantity * self.price


class InvoiceFactura(models.Model):
    """
    Счёт-фактура (бухгалтерский документ)
    """
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('issued', 'Выставлен'),
        ('cancelled', 'Отменён'),
    )

    number = models.CharField(max_length=50, unique=True, verbose_name='Номер счёта-фактуры')

    counterparty = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.PROTECT,
        related_name='invoice_facturas',
        verbose_name='Контрагент'
    )

    # Основание — может быть накладная ИЛИ акт
    expense = models.ForeignKey(
        'WarehouseExpense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_facturas',
        verbose_name='Расходная накладная'
    )
    completion_act = models.ForeignKey(
        'CompletionAct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_facturas',
        verbose_name='Акт выполненных работ'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Статус')
    factura_date = models.DateField(verbose_name='Дата выставления')

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_facturas',
        verbose_name='Создал'
    )

    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Счёт-фактура'
        verbose_name_plural = 'Счета-фактуры'
        ordering = ['-created_at']

    def __str__(self):
        return f"Счёт-фактура №{self.number} от {self.factura_date}"

    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last = InvoiceFactura.objects.filter(number__startswith=f'СФ-{date_str}').count()
            self.number = f'СФ-{date_str}-{last + 1:03d}'
        super().save(*args, **kwargs)

    @property
    def total_sum(self):
        return sum(item.total for item in self.items.all())

    @property
    def total_vat(self):
        return sum(item.vat_amount for item in self.items.all())


class InvoiceFacturaItem(models.Model):
    """
    Строка счёта-фактуры
    """
    factura = models.ForeignKey(
        InvoiceFactura,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Счёт-фактура'
    )

    description = models.CharField(max_length=200, verbose_name='Наименование')
    quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Количество')
    unit = models.CharField(max_length=20, default='шт', verbose_name='Ед. изм.')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена без НДС')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name='Ставка НДС, %')

    class Meta:
        verbose_name = 'Строка счёта-фактуры'
        verbose_name_plural = 'Строки счёта-фактуры'

    def __str__(self):
        return f"{self.description} x {self.quantity}"

    @property
    def total(self):
        return self.quantity * self.price

    @property
    def vat_amount(self):
        return self.total * self.vat_rate / 100

    @property
    def total_with_vat(self):
        return self.total + self.vat_amount
