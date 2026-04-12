from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaterialRequest, MaterialRequestItem, InventoryIssue, InventoryIssueItem, WarehouseTransfer, \
    WarehouseStocktake, InventoryWriteOff, InventoryTransfer, InventoryStocktake
from .models import WarehouseReceipt
from warehouse.models import WarehouseTransaction


@receiver(post_save, sender=MaterialRequest)
def process_material_request_issuance(sender, instance, **kwargs):
    """
    При изменении статуса на 'issued' или 'partially_issued' — списываем материалы со склада.
    """
    if instance.status in ['issued', 'partially_issued']:
        for item in instance.items.all():
            if item.issued_quantity > 0:
                # Создаём транзакцию списания
                WarehouseTransaction.objects.create(
                    item=item.warehouse_item,
                    transaction_type='out',
                    quantity=item.issued_quantity,
                    from_department=instance.department,
                    task=instance.task,
                    comment=f'Выдано по требованию №{instance.number}',
                    created_by=instance.issued_by or instance.created_by
                )

                # Уменьшаем остаток на складе
                item.warehouse_item.quantity -= item.issued_quantity
                item.warehouse_item.save()


@receiver(post_save, sender=WarehouseReceipt)
def process_receipt_conduct(sender, instance, **kwargs):
    """При проведении накладной — увеличиваем остатки на складе"""
    if instance.status == 'conducted':
        # Проверяем, не проведена ли уже (чтобы не задвоить)
        # Можно добавить флаг, но пока проще проверять по транзакциям
        for item in instance.items.all():
            # Увеличиваем остаток
            item.warehouse_item.quantity += item.quantity
            item.warehouse_item.save()

            # Создаём запись в журнале
            WarehouseTransaction.objects.get_or_create(
                item=item.warehouse_item,
                transaction_type='in',
                quantity=item.quantity,
                to_department=instance.department,
                comment=f'Поступление по накладной №{instance.number}',
                created_by=instance.conducted_by or instance.created_by,
                defaults={'created_by': instance.conducted_by or instance.created_by}
            )


@receiver(post_save, sender=InventoryIssue)
def update_inventory_status_on_issue(sender, instance, **kwargs):
    """
    При выдаче инвентаря обновляем его статус и ответственного.
    """
    if instance.status == 'issued':
        for item in instance.items.filter(returned=False):
            inv = item.inventory_item
            inv.status = 'active'  # или можно создать статус 'issued'
            inv.responsible = item.responsible
            inv.department = instance.department
            inv.save()

    elif instance.status == 'returned':
        for item in instance.items.filter(returned=True):
            inv = item.inventory_item
            inv.status = 'active'
            inv.responsible = None
            inv.save()


from .models import WarehouseExpense


@receiver(post_save, sender=WarehouseExpense)
def process_expense_conduct(sender, instance, **kwargs):
    """При проведении расходной накладной — уменьшаем остатки"""
    if instance.status == 'conducted':
        for item in instance.items.all():
            if item.warehouse_item.quantity >= item.quantity:
                item.warehouse_item.quantity -= item.quantity
                item.warehouse_item.save()

                WarehouseTransaction.objects.create(
                    item=item.warehouse_item,
                    transaction_type='out',
                    quantity=item.quantity,
                    from_department=instance.department,
                    task=instance.task,
                    comment=f'Списание по накладной №{instance.number}',
                    created_by=instance.conducted_by or instance.created_by
                )


@receiver(post_save, sender=WarehouseTransfer)
def process_transfer_conduct(sender, instance, **kwargs):
    """При проведении перемещения — переносим остатки"""
    if instance.status == 'conducted':
        for item in instance.items.all():
            if item.warehouse_item.quantity >= item.quantity:
                # Списываем с отправителя
                WarehouseTransaction.objects.create(
                    item=item.warehouse_item,
                    transaction_type='move',
                    quantity=item.quantity,
                    from_department=instance.from_department,
                    to_department=instance.to_department,
                    comment=f'Перемещение по накладной №{instance.number}',
                    created_by=instance.conducted_by or instance.created_by
                )
                # Обновляем остаток (уменьшаем на старом складе)
                item.warehouse_item.quantity -= item.quantity
                item.warehouse_item.save()


@receiver(post_save, sender=WarehouseStocktake)
def process_stocktake_conduct(sender, instance, **kwargs):
    """При проведении инвентаризации — корректируем остатки и создаём транзакции"""
    if instance.status == 'conducted':
        for item in instance.items.all():
            diff = item.actual_quantity - item.book_quantity
            if diff != 0:
                # Обновляем остаток
                item.warehouse_item.quantity = item.actual_quantity
                item.warehouse_item.save()

                # Создаём транзакцию
                WarehouseTransaction.objects.create(
                    item=item.warehouse_item,
                    transaction_type='in' if diff > 0 else 'out',
                    quantity=abs(diff),
                    to_department=instance.department if diff > 0 else None,
                    from_department=instance.department if diff < 0 else None,
                    comment=f'Корректировка по инвентаризации №{instance.number}',
                    created_by=instance.conducted_by or instance.created_by
                )


@receiver(post_save, sender=InventoryWriteOff)
def process_writeoff_conduct(sender, instance, **kwargs):
    """При проведении списания — меняем статус инвентаря"""
    if instance.status == 'conducted':
        for item in instance.items.all():
            item.inventory_item.status = 'decommissioned'
            item.inventory_item.decommission_date = instance.writeoff_date
            item.inventory_item.decommission_reason = instance.reason
            item.inventory_item.save()

@receiver(post_save, sender=InventoryTransfer)
def process_inventory_transfer_conduct(sender, instance, **kwargs):
    """При проведении перемещения — меняем отдел и ответственного"""
    if instance.status == 'conducted':
        for item in instance.items.all():
            item.inventory_item.department = instance.to_department
            item.inventory_item.responsible = item.new_responsible
            item.inventory_item.save()


@receiver(post_save, sender=InventoryStocktake)
def process_inventory_stocktake_conduct(sender, instance, **kwargs):
    """При проведении инвентаризации — корректируем статусы инвентаря"""
    if instance.status == 'conducted':
        for item in instance.items.all():
            diff = item.actual_quantity - item.book_quantity
            if diff < 0:
                # Недостача — помечаем как утерянные
                item.inventory_item.status = 'lost'
                item.inventory_item.save()
            elif diff > 0:
                # Излишки — можно создать новый инвентарь или просто отметить
                pass

