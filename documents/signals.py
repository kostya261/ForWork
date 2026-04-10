from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaterialRequest, MaterialRequestItem, InventoryIssue, InventoryIssueItem
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