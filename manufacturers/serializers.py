from rest_framework import serializers
from .models import Manufacturer


class ManufacturerSerializer(serializers.ModelSerializer):
    logo_url = serializers.ImageField(source='logo.image', read_only=True)
    inventory_count = serializers.SerializerMethodField()
    warehouse_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Manufacturer
        fields = [
            'id', 'name', 'description', 'logo', 'logo_url',
            'website', 'country', 'inventory_count', 'warehouse_items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_inventory_count(self, obj):
        return obj.inventory_items.count()

    def get_warehouse_items_count(self, obj):
        return obj.warehouse_items.count()