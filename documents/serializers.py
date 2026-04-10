from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    MaterialRequest, MaterialRequestItem,
    InventoryIssue, InventoryIssueItem
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
            'task', 'department', 'issue_date',
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