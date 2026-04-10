from rest_framework import serializers
from .models import InventoryCategory


class InventoryCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    inventory_items_count = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCategory
        fields = [
            'id', 'name', 'description', 'parent',
            'children', 'inventory_items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        if obj.children.exists():
            return InventoryCategorySerializer(obj.children.all(), many=True).data
        return []

    def get_inventory_items_count(self, obj):
        return obj.inventory_items.count()


class InventoryCategoryTreeSerializer(serializers.ModelSerializer):
    """Только дерево без лишних полей"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCategory
        fields = ['id', 'name', 'children']

    def get_children(self, obj):
        if obj.children.exists():
            return InventoryCategoryTreeSerializer(obj.children.all(), many=True).data
        return []