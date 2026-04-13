from rest_framework import serializers

from gallery.models import Image
from .models import WarehouseItem, WarehouseTransaction


class WarehouseItemListSerializer(serializers.ModelSerializer):
    """Краткая информация для списков"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = WarehouseItem
        fields = [
            'id', 'name', 'article', 'quantity', 'unit', 'unit_display',
            'category_name', 'manufacturer_name', 'department_name',
            'purchase_price', 'retail_price', 'is_low_stock'
        ]


class WarehouseItemDetailSerializer(serializers.ModelSerializer):
    """Полная информация о складской позиции"""
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=WarehouseItem._meta.get_field('category').remote_field.model.objects.all(),
        source='category', write_only=True, required=False
    )

    manufacturer = serializers.PrimaryKeyRelatedField(read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        queryset=WarehouseItem._meta.get_field('manufacturer').remote_field.model.objects.all(),
        source='manufacturer', write_only=True, required=False
    )

    department = serializers.PrimaryKeyRelatedField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=WarehouseItem._meta.get_field('department').remote_field.model.objects.all(),
        source='department', write_only=True, required=False
    )

    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    images_count = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()

    image_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Image.objects.all(),
        source='images',
        write_only=True,
        required=False
    )

    class Meta:
        model = WarehouseItem
        fields = [
            'id', 'name', 'description', 'article', 'serial_number',
            'category', 'category_name', 'category_id',
            'manufacturer', 'manufacturer_name', 'manufacturer_id',
            'quantity', 'unit', 'unit_display', 'min_stock', 'is_low_stock',
            'purchase_price', 'retail_price',
            'department', 'department_name', 'department_id',
            'images', 'image_ids','images_count',
            'recent_transactions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_images_count(self, obj):
        return obj.images.count()

    def get_recent_transactions(self, obj):
        transactions = obj.transactions.all()[:5]
        return WarehouseTransactionSerializer(transactions, many=True).data


class WarehouseTransactionSerializer(serializers.ModelSerializer):
    """Журнал движения"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    from_department_name = serializers.CharField(source='from_department.name', read_only=True)
    to_department_name = serializers.CharField(source='to_department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    task_id = serializers.IntegerField(source='task.id', read_only=True)

    class Meta:
        model = WarehouseTransaction
        fields = [
            'id', 'item', 'item_name',
            'transaction_type', 'transaction_type_display',
            'quantity',
            'from_department', 'from_department_name',
            'to_department', 'to_department_name',
            'task', 'task_id',
            'comment', 'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class WarehouseTransactionCreateSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для создания транзакции"""

    class Meta:
        model = WarehouseTransaction
        fields = [
            'item', 'transaction_type', 'quantity',
            'from_department', 'to_department', 'task', 'comment'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user

        # Создаем транзакцию
        transaction = super().create(validated_data)

        # Обновляем остаток на складе
        item = transaction.item
        if transaction.transaction_type == 'in':
            item.quantity += transaction.quantity
        elif transaction.transaction_type in ['out', 'reserve']:
            item.quantity -= transaction.quantity
        elif transaction.transaction_type == 'move':
            # При перемещении количество на складе-отправителе уменьшается
            # Но это упрощенная логика, потом можно усложнить
            item.quantity -= transaction.quantity

        item.save()

        return transaction