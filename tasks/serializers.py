from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Task, TaskStatusHistory, TaskComment,
    TaskInventoryRequirement, TaskMaterialRequirement
)

User = get_user_model()


class TaskStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)

    class Meta:
        model = TaskStatusHistory
        fields = [
            'id', 'old_status', 'old_status_display',
            'new_status', 'new_status_display',
            'changed_by', 'changed_by_name', 'comment', 'created_at'
        ]


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'author', 'author_name', 'text', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)


class TaskInventoryRequirementSerializer(serializers.ModelSerializer):
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    inventory_number = serializers.CharField(source='inventory.inventory_number', read_only=True)

    class Meta:
        model = TaskInventoryRequirement
        fields = [
            'id', 'inventory', 'inventory_name', 'inventory_number',
            'quantity', 'comment', 'created_at'
        ]


class TaskMaterialRequirementSerializer(serializers.ModelSerializer):
    warehouse_item_name = serializers.CharField(source='warehouse_item.name', read_only=True)
    warehouse_item_article = serializers.CharField(source='warehouse_item.article', read_only=True)
    warehouse_item_unit = serializers.CharField(source='warehouse_item.get_unit_display', read_only=True)
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = TaskMaterialRequirement
        fields = [
            'id', 'warehouse_item', 'warehouse_item_name',
            'warehouse_item_article', 'warehouse_item_unit',
            'planned_quantity', 'consumed_quantity', 'remaining',
            'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['consumed_quantity', 'created_at', 'updated_at']

    def get_remaining(self, obj):
        return obj.remaining_to_consume


class TaskListSerializer(serializers.ModelSerializer):
    """Краткая информация для списка задач"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    counterparty_name = serializers.CharField(source='counterparty.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'name', 'priority', 'priority_display',
            'status', 'status_display', 'is_overdue',
            'responsible', 'responsible_name',
            'department', 'department_name',
            'counterparty', 'counterparty_name',
            'deadline', 'created_by_name',
            'comments_count', 'created_at'
        ]

    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.deadline and obj.status not in ['completed', 'closed', 'cancelled']:
            return obj.deadline < timezone.now()
        return False

    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """Полная информация о задаче"""
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    responsible = serializers.PrimaryKeyRelatedField(read_only=True)
    responsible_name = serializers.CharField(source='responsible.get_full_name', read_only=True)
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='responsible', write_only=True, required=False
    )

    department = serializers.PrimaryKeyRelatedField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Task._meta.get_field('department').remote_field.model.objects.all(),
        source='department', write_only=True, required=False
    )

    counterparty = serializers.PrimaryKeyRelatedField(read_only=True)
    counterparty_name = serializers.CharField(source='counterparty.name', read_only=True)
    counterparty_id = serializers.PrimaryKeyRelatedField(
        queryset=Task._meta.get_field('counterparty').remote_field.model.objects.all(),
        source='counterparty', write_only=True, required=False
    )

    co_executors = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    co_executors_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(),
        source='co_executors', write_only=True, required=False
    )
    co_executors_names = serializers.SerializerMethodField()

    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()

    status_history = TaskStatusHistorySerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    inventory_requirements = TaskInventoryRequirementSerializer(many=True, read_only=True)
    material_requirements = TaskMaterialRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'name', 'description',
            'priority', 'priority_display',
            'status', 'status_display', 'is_overdue',
            'created_by', 'created_by_name',
            'responsible', 'responsible_name', 'responsible_id',
            'co_executors', 'co_executors_ids', 'co_executors_names',
            'department', 'department_name', 'department_id',
            'counterparty', 'counterparty_name', 'counterparty_id',
            'deadline', 'completed_at',
            'status_history', 'comments',
            'inventory_requirements', 'material_requirements',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'completed_at']

    def get_co_executors_names(self, obj):
        return [user.get_full_name() for user in obj.co_executors.all()]

    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.deadline and obj.status not in ['completed', 'closed', 'cancelled']:
            return obj.deadline < timezone.now()
        return False

    def update(self, instance, validated_data):
        """При изменении статуса автоматически создаем запись в истории"""
        old_status = instance.status
        new_status = validated_data.get('status', old_status)

        task = super().update(instance, validated_data)

        # Если статус изменился, создаем запись в истории
        if old_status != new_status:
            request = self.context.get('request')
            TaskStatusHistory.objects.create(
                task=task,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user if request else None
            )

            # Если задача выполнена, проставляем дату
            if new_status in ['completed', 'closed'] and not task.completed_at:
                from django.utils import timezone
                task.completed_at = timezone.now()
                task.save(update_fields=['completed_at'])

        return task


class TaskCreateSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для создания задачи"""

    class Meta:
        model = Task
        fields = [
            'id',
            'name', 'description', 'priority',
            'responsible', 'co_executors', 'department',
            'counterparty', 'deadline'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['status'] = 'new'

        # Создаем задачу
        task = super().create(validated_data)

        # Создаем первую запись в истории статусов
        TaskStatusHistory.objects.create(
            task=task,
            old_status='',
            new_status='new',
            changed_by=request.user,
            comment='Задача создана'
        )

        return task


class TaskStatusUpdateSerializer(serializers.Serializer):
    """Сериализатор для быстрого обновления статуса"""
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True)
