from rest_framework import serializers

from gallery.models import Image
from .models import WarehouseRack, WarehouseCell


class WarehouseCellSerializer(serializers.ModelSerializer):
    rack_name = serializers.CharField(source='rack.name', read_only=True)
    rack_number = serializers.CharField(source='rack.number', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseCell
        fields = [
            'id', 'rack', 'rack_name', 'rack_number',
            'name', 'number', 'description',
            'width', 'height', 'depth', 'max_weight',
            'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.count()


class WarehouseCellListSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для списка"""
    rack_name = serializers.CharField(source='rack.name', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseCell
        fields = ['id', 'rack', 'rack_name', 'name', 'number', 'items_count']

    def get_items_count(self, obj):
        return obj.items.count()


class WarehouseRackSerializer(serializers.ModelSerializer):
    cells = WarehouseCellSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    cells_count = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseRack
        fields = [
            'id', 'department', 'department_name',
            'name', 'number', 'description',
            'cells', 'cells_count',
            'images', 'images_urls',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_cells_count(self, obj):
        return obj.cells.count()

    def get_images_urls(self, obj):
        request = self.context.get('request')
        urls = []
        for img in obj.images.all():
            if img.image and request:
                urls.append(request.build_absolute_uri(img.image.url))
        return urls


class WarehouseRackCreateSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=WarehouseRack._meta.get_field('department').remote_field.model.objects.all(),
        source='department',
        write_only=True
    )

    image_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Image.objects.all(),
        source='images',
        write_only=True,
        required=False
    )

    class Meta:
        model = WarehouseRack
        fields = ['id', 'department_id', 'name', 'number', 'description', 'image_ids']
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        images = validated_data.pop('images', [])
        validated_data['created_by'] = request.user
        rack = WarehouseRack.objects.create(**validated_data)
        if images:
            rack.images.set(images)
        return rack


class WarehouseCellCreateSerializer(serializers.ModelSerializer):
    rack_id = serializers.PrimaryKeyRelatedField(
        queryset=WarehouseRack.objects.all(),
        source='rack',
        write_only=True
    )

    image_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Image.objects.all(),
        source='images',
        write_only=True,
        required=False
    )

    class Meta:
        model = WarehouseCell
        fields = ['id', 'rack_id', 'name', 'number', 'description',
                  'width', 'height', 'depth', 'max_weight', 'image_ids']
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)