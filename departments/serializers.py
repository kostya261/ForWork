from rest_framework import serializers
from django.contrib.auth import get_user_model
from banks.models import Bank
from departments.models import Department

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    head_name = serializers.CharField(source='head.get_full_name', read_only=True)

    # Поля для записи
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='parent',
        write_only=True,
        required=False,
        allow_null=True
    )
    head_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='head',
        write_only=True,
        required=False,
        allow_null=True
    )
    # Банковские реквизиты
    bank_id = serializers.PrimaryKeyRelatedField(
        queryset=Bank.objects.all(),
        source='bank',
        write_only=True,
        required=False,
        allow_null=True
    )
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description',
            'legal_address', 'actual_address',
            'inn', 'kpp', 'ogrn',  # 🔥 Добавили реквизиты
            'parent', 'parent_id', 'children',
            'head', 'head_id', 'head_name',
            'created_at', 'updated_at',
            'bank', 'bank_id', 'bank_name', 'bank_account',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        if obj.children.exists():
            return DepartmentSerializer(obj.children.all(), many=True).data
        return []