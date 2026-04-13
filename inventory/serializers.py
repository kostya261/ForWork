from rest_framework import serializers

from gallery.models import Image
from inventory_categories.models import InventoryCategory
from .models import InventoryItem


class InventoryItemListSerializer(serializers.ModelSerializer):
    """Краткая информация для списков"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    image_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Image.objects.all(),
        source='images',
        write_only=True,
        required=False
    )

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'inventory_number', 'serial_number',
            'category_name', 'image_ids',
            'manufacturer_name', 'status', 'status_display',
            'department_name', 'responsible_name',
            'purchase_price', 'purchase_date'
        ]


class InventoryItemDetailSerializer(serializers.ModelSerializer):
    """Полная информация об инвентаре"""
    manufacturer = serializers.PrimaryKeyRelatedField(read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem._meta.get_field('manufacturer').remote_field.model.objects.all(),
        source='manufacturer', write_only=True, required=False
    )

    department = serializers.PrimaryKeyRelatedField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem._meta.get_field('department').remote_field.model.objects.all(),
        source='department', write_only=True, required=False
    )

    responsible = serializers.PrimaryKeyRelatedField(read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItem._meta.get_field('responsible').remote_field.model.objects.all(),
        source='responsible', write_only=True, required=False
    )

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    images_count = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()

    category = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=InventoryCategory.objects.all(),
        source='category', write_only=True, required=False
    )

    # 🔥 ВОТ ЭТО ДОБАВЛЯЕМ — для приёма ID изображений при создании/редактировании
    image_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Image.objects.all(),
        source='images',
        write_only=True,
        required=False
    )

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'name', 'description',
            'category', 'category_name', 'category_id',
            'manufacturer', 'manufacturer_name', 'manufacturer_id',
            'serial_number', 'inventory_number',
            'production_date', 'purchase_date', 'receipt_date', 'decommission_date',
            'purchase_price',
            'status', 'status_display', 'decommission_reason',
            'department', 'department_name', 'department_id',
            'responsible', 'responsible_name', 'responsible_id',
            'images', 'image_ids',  # 🔥 и в fields добавляем
            'images_count', 'images_urls',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_images_count(self, obj):
        return obj.images.count()

    def get_images_urls(self, obj):
        request = self.context.get('request')
        urls = []
        for img in obj.images.all():
            if img.image and request:
                urls.append(request.build_absolute_uri(img.image.url))
        return urls