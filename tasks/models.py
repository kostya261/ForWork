from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Task(models.Model):
    """
    Задача / Заявка на выполнение работ.
    """
    PRIORITY_CHOICES = (
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
        ('critical', 'Критическая'),
    )

    STATUS_CHOICES = (
        ('new', 'Новая'),
        ('assigned', 'Назначена'),
        ('in_progress', 'В работе'),
        ('paused', 'Приостановлена'),
        ('completed', 'Выполнена'),
        ('closed', 'Закрыта'),
        ('cancelled', 'Отменена'),
    )

    # Основная информация
    name = models.CharField(max_length=200, verbose_name='Наименование задачи')
    description = models.TextField(blank=True, verbose_name='Описание задачи')

    # Срочность и статус
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Срочность')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new', verbose_name='Статус')

    # Кто и когда
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='Кто создал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    # Сроки
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата выполнения')

    # Ответственные
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_tasks',
        verbose_name='Ответственный'
    )
    co_executors = models.ManyToManyField(
        User,
        blank=True,
        related_name='co_executed_tasks',
        verbose_name='Соисполнители'
    )

    # Связь с контрагентом
    counterparty = models.ForeignKey(
        'counterparties.Counterparty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Контрагент'
    )

    # Отдел (для фильтрации и прав)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Отдел'
    )

    # Служебные поля
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']

    @property
    def status_color(self):
        colors = {
            'new': 'secondary',
            'assigned': 'primary',
            'in_progress': 'warning',
            'paused': 'purple',
            'completed': 'success',
            'closed': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

    @property
    def priority_color(self):
        colors = {
            'low': 'success',
            'medium': 'primary',
            'high': 'warning',
            'critical': 'danger',
        }
        return colors.get(self.priority, 'secondary')

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.deadline and self.status not in ['completed', 'closed', 'cancelled']:
            return self.deadline < timezone.now()
        return False

    def __str__(self):
        return f"Задача #{self.pk}: {self.name}"


class TaskStatusHistory(models.Model):
    """
    История изменения статусов задачи.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Задача'
    )
    old_status = models.CharField(max_length=15, choices=Task.STATUS_CHOICES, blank=True,
                                  verbose_name='Предыдущий статус')
    new_status = models.CharField(max_length=15, choices=Task.STATUS_CHOICES, verbose_name='Новый статус')
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_changes',
        verbose_name='Кто изменил'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения')

    class Meta:
        verbose_name = 'История статуса задачи'
        verbose_name_plural = 'История статусов задач'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task} | {self.old_status} → {self.new_status}"


class TaskComment(models.Model):
    """
    Комментарии к задаче.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Комментарий к задаче'
        verbose_name_plural = 'Комментарии к задачам'
        ordering = ['created_at']

    def __str__(self):
        return f"Комментарий от {self.author} к {self.task}"


class TaskInventoryRequirement(models.Model):
    """
    Необходимый инвентарь (оборудование) для выполнения задачи.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='inventory_requirements',
        verbose_name='Задача'
    )
    inventory = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='task_requirements',
        verbose_name='Инвентарь'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество (шт.)')
    comment = models.CharField(max_length=200, blank=True, verbose_name='Примечание')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Требуемый инвентарь'
        verbose_name_plural = 'Требуемый инвентарь'
        unique_together = ['task', 'inventory']

    def __str__(self):
        return f"{self.inventory.name} ({self.quantity} шт.) для {self.task}"


class TaskMaterialRequirement(models.Model):
    """
    Необходимые расходные материалы для выполнения задачи.
    Списываются со склада.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='material_requirements',
        verbose_name='Задача'
    )
    warehouse_item = models.ForeignKey(
        'warehouse.WarehouseItem',
        on_delete=models.PROTECT,
        related_name='task_requirements',
        verbose_name='Расходник'
    )
    planned_quantity = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Плановое количество')
    consumed_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0,
                                            verbose_name='Списано фактически')
    comment = models.CharField(max_length=200, blank=True, verbose_name='Примечание')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Требуемый материал'
        verbose_name_plural = 'Требуемые материалы'
        unique_together = ['task', 'warehouse_item']

    def __str__(self):
        return f"{self.warehouse_item.name} ({self.planned_quantity}) для {self.task}"

    @property
    def remaining_to_consume(self):
        """Сколько еще осталось списать"""
        return self.planned_quantity - self.consumed_quantity
