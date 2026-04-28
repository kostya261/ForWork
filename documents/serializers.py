from rest_framework import serializers
from django.contrib.auth import get_user_model

from inventory.models import InventoryItem
from warehouse.models import WarehouseItem
from .models import (
    MaterialRequest, MaterialRequestItem,
    InventoryIssue, InventoryIssueItem, WarehouseReceipt, WarehouseReceiptItem, WarehouseExpense, WarehouseExpenseItem,
    WarehouseTransferItem, WarehouseTransfer, WarehouseStocktakeItem, WarehouseStocktake, InventoryWriteOff,
    InventoryWriteOffItem, InventoryTransfer, InventoryTransferItem, InventoryStocktakeItem, InventoryStocktake,
    CompletionAct, CompletionActMaterial, InvoiceFacturaItem, InvoiceFactura
)

User = get_user_model()


# ========== MaterialRequest ==========

class MaterialRequestItemSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)
    warehouse_item_article = serializers.CharField(source='warehouse_item.article', read_only=True)
    warehouse_item_unit = serializers.CharField(source='warehouse_item.get_unit_display', read_only=True)
    available_quantity = serializers.SerializerMethodField()
    remaining_to_issue = serializers.SerializerMethodField()

    class Meta:
        model = MaterialRequestItem
        fields = [
            'id', 'warehouse_item', 'warehouse_item_name',
            'warehouse_item_article', 'warehouse_item_unit',
            'requested_quantity', 'issued_quantity',
            'available_quantity', 'remaining_to_issue',
            'comment'
        ]
        read_only_fields = ['issued_quantity']

    def get_available_quantity(self, obj):
        return obj.warehouse_item.quantity

    def get_remaining_to_issue(self, obj):
        return obj.requested_quantity - obj.issued_quantity


class MaterialRequestListSerializer(serializers.ModelSerializer):
    """Краткая информация для списка"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    task_id = serializers.IntegerField(source='task.id', read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = MaterialRequest
        fields = [
            'id', 'number', 'task_id', 'task_name',
            'department', 'department_name',
            'status', 'status_display',
            'requested_date', 'items_count',
            'created_by', 'created_by_name',
            'created_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class MaterialRequestDetailSerializer(serializers.ModelSerializer):
    """Полная информация с позициями"""
    department = serializers.PrimaryKeyRelatedField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=MaterialRequest._meta.get_field('department').remote_field.model.objects.all(),
        source='department', write_only=True, required=False
    )

    task = serializers.PrimaryKeyRelatedField(read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=MaterialRequest._meta.get_field('task').remote_field.model.objects.all(),
        source='task', write_only=True, required=False
    )

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.get_full_name', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = MaterialRequestItemSerializer(many=True, read_only=True)

    class Meta:
        model = MaterialRequest
        fields = [
            'id', 'number', 'task', 'task_name', 'task_id',
            'department', 'department_name', 'department_id',
            'status', 'status_display',
            'requested_date', 'issued_date',
            'created_by', 'created_by_name',
            'approved_by', 'approved_by_name',
            'issued_by', 'issued_by_name',
            'comment', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['number', 'created_by', 'created_at', 'updated_at']


class MaterialRequestCreateSerializer(serializers.ModelSerializer):
    """Создание требования с позициями"""
    items = MaterialRequestItemSerializer(many=True)

    class Meta:
        model = MaterialRequest
        fields = [
            'task', 'department', 'requested_date',
            'comment', 'items'
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Требование должно содержать хотя бы одну позицию')
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        validated_data['created_by'] = request.user
        validated_data['status'] = 'draft'

        material_request = MaterialRequest.objects.create(**validated_data)

        for item_data in items_data:
            MaterialRequestItem.objects.create(request=material_request, **item_data)

        return material_request


class MaterialRequestUpdateStatusSerializer(serializers.Serializer):
    """Изменение статуса требования"""
    status = serializers.ChoiceField(choices=[
        ('pending', 'Ожидает одобрения'),
        ('approved', 'Одобрено'),
        ('issued', 'Выдано'),
        ('cancelled', 'Отменено'),
    ])
    comment = serializers.CharField(required=False, allow_blank=True)


class IssueMaterialItemSerializer(serializers.Serializer):
    """Выдача конкретной позиции"""
    item_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=3)


# ========== InventoryIssue ==========

class InventoryIssueItemSerializer(serializers.ModelSerializer):
    inventory_name = serializers.CharField(source='inventory_item.name', read_only=True)
    inventory_number = serializers.CharField(source='inventory_item.inventory_number', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)

    class Meta:
        model = InventoryIssueItem
        fields = [
            'id', 'inventory_item', 'inventory_name', 'inventory_number',
            'quantity', 'responsible', 'responsible_name',
            'returned', 'comment'
        ]


class InventoryIssueListSerializer(serializers.ModelSerializer):
    """Краткая информация для списка"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    task_id = serializers.IntegerField(source='task.id', read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = InventoryIssue
        fields = [
            'id', 'number', 'task_id', 'task_name',
            'department', 'department_name',
            'status', 'status_display',
            'issue_date', 'items_count',
            'created_by', 'created_by_name',
            'created_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class InventoryIssueDetailSerializer(serializers.ModelSerializer):
    """Полная информация с позициями"""
    department = serializers.PrimaryKeyRelatedField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryIssue._meta.get_field('department').remote_field.model.objects.all(),
        source='department', write_only=True, required=False
    )

    task = serializers.PrimaryKeyRelatedField(read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryIssue._meta.get_field('task').remote_field.model.objects.all(),
        source='task', write_only=True, required=False
    )

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.get_full_name', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = InventoryIssueItemSerializer(many=True, read_only=True)

    class Meta:
        model = InventoryIssue
        fields = [
            'id', 'number', 'task', 'task_name', 'task_id',
            'department', 'department_name', 'department_id',
            'status', 'status_display',
            'issue_date', 'return_date',
            'created_by', 'created_by_name',
            'approved_by', 'approved_by_name',
            'issued_by', 'issued_by_name',
            'comment', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['number', 'created_by', 'created_at', 'updated_at']


class InventoryIssueCreateSerializer(serializers.ModelSerializer):
    """Создание накладной с позициями"""
    items = InventoryIssueItemSerializer(many=True)

    class Meta:
        model = InventoryIssue
        fields = [
            'id', 'task', 'department', 'issue_date',
            'comment', 'items'
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Накладная должна содержать хотя бы одну позицию')
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        validated_data['created_by'] = request.user
        validated_data['status'] = 'draft'

        issue = InventoryIssue.objects.create(**validated_data)

        for item_data in items_data:
            InventoryIssueItem.objects.create(issue=issue, **item_data)

        return issue


class InventoryIssueUpdateStatusSerializer(serializers.Serializer):
    """Изменение статуса накладной"""
    status = serializers.ChoiceField(choices=[
        ('pending', 'Ожидает одобрения'),
        ('approved', 'Одобрено'),
        ('issued', 'Выдано'),
        ('returned', 'Возвращено'),
        ('cancelled', 'Отменено'),
    ])
    comment = serializers.CharField(required=False, allow_blank=True)


class ReturnInventoryItemSerializer(serializers.Serializer):
    """Возврат инвентаря"""
    item_id = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True)


class WarehouseReceiptItemSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = WarehouseReceiptItem
        fields = ['id', 'warehouse_item', 'warehouse_item_name', 'quantity', 'price', 'total']


class WarehouseReceiptSerializer(serializers.ModelSerializer):
    items = WarehouseReceiptItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = WarehouseReceipt
        fields = [
            'id', 'number', 'supplier', 'supplier_name',
            'department', 'department_name',
            'status', 'receipt_date',
            'items', 'total_sum', 'comment',
            'created_by', 'created_at'
        ]
        read_only_fields = ['number', 'created_by', 'created_at']


class WarehouseReceiptCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = WarehouseReceipt
        fields = ['id', 'supplier', 'department', 'receipt_date', 'comment', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        # Создаём без created_by в validated_data
        receipt = WarehouseReceipt(
            supplier=validated_data['supplier'],
            department=validated_data['department'],
            receipt_date=validated_data.get('receipt_date'),
            comment=validated_data.get('comment', ''),
            created_by=request.user
        )
        receipt.save()

        for item_data in items_data:
            WarehouseReceiptItem.objects.create(
                receipt=receipt,
                warehouse_item_id=item_data['warehouse_item_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )

        return receipt


class WarehouseExpenseItemSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = WarehouseExpenseItem
        fields = ['id', 'warehouse_item', 'warehouse_item_name', 'quantity', 'price', 'total']


class WarehouseExpenseSerializer(serializers.ModelSerializer):
    items = WarehouseExpenseItemSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    counterparty_name = serializers.CharField(source='counterparty.name', read_only=True)
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = WarehouseExpense
        fields = ['id', 'number', 'department', 'department_name', 'counterparty', 'counterparty_name',
                  'task', 'status', 'expense_date', 'items', 'total_sum', 'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class WarehouseExpenseCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = WarehouseExpense
        fields = ['id', 'department', 'counterparty', 'task', 'expense_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        expense = WarehouseExpense(
            created_by=request.user,
            **validated_data
        )
        expense.save()

        for item_data in items_data:
            WarehouseExpenseItem.objects.create(
                expense=expense,
                warehouse_item_id=item_data['warehouse_item_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )

        return expense


class WarehouseTransferItemSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)

    class Meta:
        model = WarehouseTransferItem
        fields = ['id', 'warehouse_item', 'warehouse_item_name', 'quantity']


class WarehouseTransferSerializer(serializers.ModelSerializer):
    items = WarehouseTransferItemSerializer(many=True, read_only=True)
    from_department_name = serializers.CharField(source='from_department.name', read_only=True)
    to_department_name = serializers.CharField(source='to_department.name', read_only=True)

    class Meta:
        model = WarehouseTransfer
        fields = ['id', 'number', 'from_department', 'from_department_name', 'to_department', 'to_department_name',
                  'status', 'transfer_date', 'items', 'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class WarehouseTransferCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = WarehouseTransfer
        fields = ['id', 'from_department', 'to_department', 'transfer_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        transfer = WarehouseTransfer.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            WarehouseTransferItem.objects.create(
                transfer=transfer,
                warehouse_item_id=item_data['warehouse_item_id'],
                quantity=item_data['quantity']
            )

        return transfer


class WarehouseStocktakeItemSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)
    difference = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = WarehouseStocktakeItem
        fields = ['id', 'warehouse_item', 'warehouse_item_name', 'book_quantity', 'actual_quantity', 'difference']


class WarehouseStocktakeSerializer(serializers.ModelSerializer):
    items = WarehouseStocktakeItemSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = WarehouseStocktake
        fields = ['id', 'number', 'department', 'department_name', 'status', 'stocktake_date',
                  'items', 'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class WarehouseStocktakeCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = WarehouseStocktake
        fields = ['id', 'department', 'stocktake_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        stocktake = WarehouseStocktake.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            # Получаем текущий остаток как учётное количество
            warehouse_item = WarehouseItem.objects.get(id=item_data['warehouse_item_id'])
            WarehouseStocktakeItem.objects.create(
                stocktake=stocktake,
                warehouse_item=warehouse_item,
                book_quantity=warehouse_item.quantity,
                actual_quantity=item_data['actual_quantity']
            )

        return stocktake


class InventoryWriteOffItemSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source='inventory_item.name', read_only=True)
    inventory_number = serializers.CharField(source='inventory_item.inventory_number', read_only=True)

    class Meta:
        model = InventoryWriteOffItem
        fields = ['id', 'inventory_item', 'inventory_item_name', 'inventory_number', 'quantity']


class InventoryWriteOffSerializer(serializers.ModelSerializer):
    items = InventoryWriteOffItemSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = InventoryWriteOff
        fields = ['id', 'number', 'department', 'department_name', 'status', 'writeoff_date', 'reason',
                  'items', 'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class InventoryWriteOffCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = InventoryWriteOff
        fields = ['id', 'department', 'writeoff_date', 'reason', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        writeoff = InventoryWriteOff.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            InventoryWriteOffItem.objects.create(
                writeoff=writeoff,
                inventory_item_id=item_data['inventory_item'],
                quantity=item_data['quantity']
            )

        return writeoff


class InventoryTransferItemSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source='inventory_item.name', read_only=True)
    inventory_number = serializers.CharField(source='inventory_item.inventory_number', read_only=True)
    new_responsible_name = serializers.CharField(source='new_responsible.get_full_name', read_only=True)

    class Meta:
        model = InventoryTransferItem
        fields = ['id', 'inventory_item', 'inventory_item_name', 'inventory_number', 'quantity', 'new_responsible',
                  'new_responsible_name']


class InventoryTransferSerializer(serializers.ModelSerializer):
    items = InventoryTransferItemSerializer(many=True, read_only=True)
    from_department_name = serializers.CharField(source='from_department.name', read_only=True)
    to_department_name = serializers.CharField(source='to_department.name', read_only=True)

    class Meta:
        model = InventoryTransfer
        fields = ['id', 'number', 'from_department', 'from_department_name', 'to_department', 'to_department_name',
                  'status', 'transfer_date', 'items', 'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class InventoryTransferCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = InventoryTransfer
        fields = ['id', 'from_department', 'to_department', 'transfer_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        transfer = InventoryTransfer.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            InventoryTransferItem.objects.create(
                transfer=transfer,
                inventory_item_id=item_data['inventory_item'],
                quantity=item_data['quantity'],
                new_responsible_id=item_data['new_responsible']
            )

        return transfer


class InventoryStocktakeItemSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source='inventory_item.name', read_only=True)
    inventory_number = serializers.CharField(source='inventory_item.inventory_number', read_only=True)
    difference = serializers.IntegerField(read_only=True)

    class Meta:
        model = InventoryStocktakeItem
        fields = ['id', 'inventory_item', 'inventory_item_name', 'inventory_number', 'book_quantity', 'actual_quantity',
                  'difference']


class InventoryStocktakeSerializer(serializers.ModelSerializer):
    items = InventoryStocktakeItemSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = InventoryStocktake
        fields = ['id', 'number', 'department', 'department_name', 'status', 'stocktake_date', 'items', 'comment',
                  'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class InventoryStocktakeCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = InventoryStocktake
        fields = ['id', 'department', 'stocktake_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        stocktake = InventoryStocktake.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            # Учётное количество — текущий остаток
            inventory_item = InventoryItem.objects.get(id=item_data['inventory_item'])
            InventoryStocktakeItem.objects.create(
                stocktake=stocktake,
                inventory_item=inventory_item,
                book_quantity=1,  # Для ОС всегда 1 штука
                actual_quantity=item_data['actual_quantity']
            )

        return stocktake


from .models import WorkOrder, WorkOrderMaterial, WorkOrderInventory


class WorkOrderMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderMaterial
        fields = ['warehouse_item', 'planned_quantity']


class WorkOrderInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderInventory
        fields = ['inventory_item', 'quantity']


class WorkOrderSerializer(serializers.ModelSerializer):
    materials = WorkOrderMaterialSerializer(many=True, read_only=True)
    inventory = WorkOrderInventorySerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = ['id', 'number', 'task', 'status', 'issue_date', 'comment', 'materials', 'inventory', 'created_by',
                  'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class WorkOrderCreateSerializer(serializers.ModelSerializer):
    materials = serializers.JSONField(write_only=True, required=False)
    inventory = serializers.JSONField(write_only=True, required=False)
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='responsible', write_only=True, required=False
    )

    class Meta:
        model = WorkOrder
        fields = ['id', 'task', 'issue_date', 'comment', 'materials', 'inventory', 'responsible_id']
        read_only_fields = ['id']

    def create(self, validated_data):
        mats = validated_data.pop('materials', [])
        invs = validated_data.pop('inventory', [])
        request = self.context.get('request')

        order = WorkOrder.objects.create(
            created_by=request.user,
            **validated_data
        )

        for m in mats:
            WorkOrderMaterial.objects.create(
                work_order=order,
                warehouse_item_id=m['warehouse_item'],  # ← исправлено
                planned_quantity=m['planned_quantity']
            )
        for i in invs:
            WorkOrderInventory.objects.create(
                work_order=order,
                inventory_item_id=i['inventory_item'],  # ← исправлено
                quantity=i['quantity']
            )

        return order


class CompletionActMaterialSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)

    class Meta:
        model = CompletionActMaterial
        fields = ['warehouse_item', 'warehouse_item_name', 'actual_quantity']


class CompletionActSerializer(serializers.ModelSerializer):
    materials = CompletionActMaterialSerializer(many=True, read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = CompletionAct
        fields = ['id', 'number', 'task', 'task_name', 'work_order', 'status',
                  'completion_date', 'materials', 'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class CompletionActCreateSerializer(serializers.ModelSerializer):
    materials = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = CompletionAct
        fields = ['id', 'task', 'work_order', 'completion_date', 'comment', 'materials']
        read_only_fields = ['id']

    def create(self, validated_data):
        mats = validated_data.pop('materials', [])
        request = self.context.get('request')

        act = CompletionAct.objects.create(
            created_by=request.user,
            **validated_data
        )

        for m in mats:
            CompletionActMaterial.objects.create(
                act=act,
                warehouse_item_id=m['warehouse_item'],
                actual_quantity=m['actual_quantity']
            )

        return act


from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ['id', 'warehouse_item', 'warehouse_item_name', 'description',
                  'quantity', 'unit', 'price', 'total']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    counterparty_name = serializers.CharField(source='counterparty.name', read_only=True)
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'number', 'counterparty', 'counterparty_name', 'task',
                  'status', 'invoice_date', 'due_date', 'items', 'total_sum',
                  'comment', 'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'counterparty', 'task', 'invoice_date', 'due_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        invoice = Invoice.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                warehouse_item_id=item_data.get('warehouse_item'),
                description=item_data.get('description', ''),
                quantity=item_data['quantity'],
                unit=item_data.get('unit', 'шт'),
                price=item_data['price']
            )

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Обновляем основные поля
        instance.counterparty = validated_data.get('counterparty', instance.counterparty)
        instance.task = validated_data.get('task', instance.task)
        instance.invoice_date = validated_data.get('invoice_date', instance.invoice_date)
        instance.due_date = validated_data.get('due_date', instance.due_date)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save()

        # Если переданы новые позиции — удаляем старые и создаём новые
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                InvoiceItem.objects.create(
                    invoice=instance,
                    warehouse_item_id=item_data.get('warehouse_item'),
                    description=item_data.get('description', ''),
                    quantity=item_data['quantity'],
                    unit=item_data.get('unit', 'шт'),
                    price=item_data['price']
                )

        return instance

class InvoiceFacturaItemSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    vat_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_with_vat = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceFacturaItem
        fields = ['id', 'description', 'quantity', 'unit', 'price', 'vat_rate',
                  'total', 'vat_amount', 'total_with_vat']


class InvoiceFacturaSerializer(serializers.ModelSerializer):
    items = InvoiceFacturaItemSerializer(many=True, read_only=True)
    counterparty_name = serializers.CharField(source='counterparty.name', read_only=True)
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_vat = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceFactura
        fields = ['id', 'number', 'counterparty', 'counterparty_name', 'expense', 'completion_act',
                  'status', 'factura_date', 'items', 'total_sum', 'total_vat', 'comment',
                  'created_by', 'created_at']
        read_only_fields = ['number', 'created_by', 'created_at']


class InvoiceFacturaCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)

    class Meta:
        model = InvoiceFactura
        fields = ['id', 'counterparty', 'expense', 'completion_act', 'factura_date', 'comment', 'items']
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')

        factura = InvoiceFactura.objects.create(
            created_by=request.user,
            **validated_data
        )

        for item_data in items_data:
            InvoiceFacturaItem.objects.create(
                factura=factura,
                description=item_data['description'],
                quantity=item_data['quantity'],
                unit=item_data.get('unit', 'шт'),
                price=item_data['price'],
                vat_rate=item_data.get('vat_rate', 20.00)
            )

        return factura

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Обновляем основные поля
        instance.counterparty = validated_data.get('counterparty', instance.counterparty)
        instance.expense = validated_data.get('expense', instance.expense)
        instance.completion_act = validated_data.get('completion_act', instance.completion_act)
        instance.factura_date = validated_data.get('factura_date', instance.factura_date)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save()

        # Если переданы новые позиции — удаляем старые и создаём новые
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                InvoiceFacturaItem.objects.create(
                    factura=instance,
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit=item_data.get('unit', 'шт'),
                    price=item_data['price'],
                    vat_rate=item_data.get('vat_rate', 20.00)
                )

        return instance