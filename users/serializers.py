from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User
from positions.models import Position
from departments.models import Department

User = get_user_model()


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


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

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description',
            'legal_address', 'actual_address',
            'parent', 'parent_id', 'children',
            'head', 'head_id', 'head_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        if obj.children.exists():
            return DepartmentSerializer(obj.children.all(), many=True).data
        return []


class UserListSerializer(serializers.ModelSerializer):
    """Краткая информация о пользователе (для списков)"""
    full_name = serializers.SerializerMethodField()
    position_name = serializers.CharField(source='position.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone',
            'position', 'position_name', 'department', 'department_name',
            'is_active', 'has_transport'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserDetailSerializer(serializers.ModelSerializer):
    """Полная информация о пользователе"""
    full_name = serializers.SerializerMethodField()
    position = PositionSerializer(read_only=True)
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), source='position', write_only=True, required=False
    )
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source='department', write_only=True, required=False
    )
    photo_url = serializers.ImageField(source='photo.image', read_only=True)
    headed_departments = DepartmentSerializer(many=True, read_only=True)
    responsible_inventory_count = serializers.SerializerMethodField()
    responsible_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'middle_name',
            'full_name', 'email', 'phone', 'telegram', 'whatsapp',
            'position', 'position_id', 'department', 'department_id',
            'passport_series', 'passport_number', 'passport_issued_by', 'passport_issued_date',
            'has_transport', 'transport_description', 'comment',
            'photo', 'photo_url', 'headed_departments',
            'responsible_inventory_count', 'responsible_tasks_count',
            'is_active', 'is_staff', 'is_superuser',
            'last_login', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'passport_series': {'write_only': True},
            'passport_number': {'write_only': True},
            'passport_issued_by': {'write_only': True},
            'passport_issued_date': {'write_only': True},
        }

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_responsible_inventory_count(self, obj):
        return obj.responsible_inventory.count()

    def get_responsible_tasks_count(self, obj):
        return obj.responsible_tasks.count()

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserMeSerializer(UserDetailSerializer):
    """Сериализатор для эндпоинта /api/users/me/"""

    class Meta(UserDetailSerializer.Meta):
        read_only_fields = ['is_active', 'is_staff', 'is_superuser']