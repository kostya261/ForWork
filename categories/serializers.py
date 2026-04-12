from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    warehouse_items_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    # Поле для записи родительской категории
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='parent',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'parent_id', 'parent_name',
            'children', 'warehouse_items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []

    def get_warehouse_items_count(self, obj):
        return obj.warehouse_items.count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Только дерево без лишних полей"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'children']

    def get_children(self, obj):
        if obj.children.exists():
            return CategoryTreeSerializer(obj.children.all(), many=True).data
        return []