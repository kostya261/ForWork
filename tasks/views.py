from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import (
    Task, TaskComment, TaskInventoryRequirement,
    TaskMaterialRequirement, TaskStatusHistory
)
from .serializers import (
    TaskListSerializer, TaskDetailSerializer, TaskCreateSerializer,
    TaskStatusUpdateSerializer, TaskCommentSerializer,
    TaskInventoryRequirementSerializer, TaskMaterialRequirementSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related(
        'created_by', 'responsible', 'department', 'counterparty'
    ).prefetch_related(
        'co_executors', 'comments', 'status_history',
        'inventory_requirements', 'material_requirements'
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'department', 'responsible', 'counterparty']
    search_fields = ['name', 'description', 'id']
    ordering_fields = ['name', 'priority', 'status', 'deadline', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        if self.action == 'create':
            return TaskCreateSerializer
        if self.action == 'update_status':
            return TaskStatusUpdateSerializer
        return TaskDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по умолчанию: показываем задачи своего отдела (если не менеджер)
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            if user.department:
                queryset = queryset.filter(department=user.department)

        # Фильтр по срокам
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                deadline__lt=timezone.now()
            ).exclude(status__in=['completed', 'closed', 'cancelled'])

        my_tasks = self.request.query_params.get('my')
        if my_tasks == 'true':
            queryset = queryset.filter(responsible=user)

        return queryset

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Быстрое обновление статуса с комментарием"""
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = task.status
        new_status = serializer.validated_data['status']
        comment = serializer.validated_data.get('comment', '')

        task.status = new_status
        if new_status in ['completed', 'closed'] and not task.completed_at:
            task.completed_at = timezone.now()
        task.save()

        # Запись в историю
        TaskStatusHistory.objects.create(
            task=task,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            comment=comment
        )

        return Response(TaskDetailSerializer(task).data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Работа с комментариями задачи"""
        task = self.get_object()

        if request.method == 'GET':
            comments = task.comments.all()
            serializer = TaskCommentSerializer(comments, many=True)
            return Response(serializer.data)

        # POST - создать комментарий
        serializer = TaskCommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_material(self, request, pk=None):
        """Добавить требование по материалам"""
        task = self.get_object()
        serializer = TaskMaterialRequirementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def consume_material(self, request, pk=None):
        """Списать материал на задачу"""
        task = self.get_object()
        requirement_id = request.data.get('requirement_id')
        quantity = request.data.get('quantity')

        try:
            req = task.material_requirements.get(id=requirement_id)
        except TaskMaterialRequirement.DoesNotExist:
            return Response({'error': 'Требование не найдено'}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем остаток на складе
        if req.warehouse_item.quantity < quantity:
            return Response(
                {'error': f'Недостаточно на складе. Доступно: {req.warehouse_item.quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем списанное количество
        req.consumed_quantity += quantity
        req.save()

        # Создаем транзакцию на складе
        from warehouse.models import WarehouseTransaction
        WarehouseTransaction.objects.create(
            item=req.warehouse_item,
            transaction_type='out',
            quantity=quantity,
            from_department=task.department,
            task=task,
            comment=f'Списание на задачу #{task.id}: {task.name}',
            created_by=request.user
        )

        # Уменьшаем остаток на складе
        req.warehouse_item.quantity -= quantity
        req.warehouse_item.save()

        return Response(TaskMaterialRequirementSerializer(req).data)

    @action(detail=True, methods=['post'])
    def add_inventory(self, request, pk=None):
        """Добавить требование по инвентарю"""
        task = self.get_object()
        serializer = TaskInventoryRequirementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по задачам"""
        user = request.user
        base_qs = self.get_queryset()

        stats = {
            'total': base_qs.count(),
            'by_status': {},
            'by_priority': {},
            'overdue': base_qs.filter(
                deadline__lt=timezone.now()
            ).exclude(status__in=['completed', 'closed', 'cancelled']).count(),
            'my_tasks': base_qs.filter(responsible=user).count(),
            'unread_comments': 0,  # Можно добавить позже
        }

        for status, label in Task.STATUS_CHOICES:
            stats['by_status'][status] = base_qs.filter(status=status).count()

        for priority, label in Task.PRIORITY_CHOICES:
            stats['by_priority'][priority] = base_qs.filter(priority=priority).count()

        return Response(stats)


    @action(detail=True, methods=['delete'], url_path='remove-material/(?P<requirement_id>[^/.]+)')
    def remove_material(self, request, pk=None, requirement_id=None):
        """Удалить требование по материалу"""
        task = self.get_object()
        try:
            req = task.material_requirements.get(id=requirement_id)
            req.delete()
            return Response({'status': 'ok'})
        except TaskMaterialRequirement.DoesNotExist:
            return Response({'error': 'Требование не найдено'}, status=404)

    @action(detail=True, methods=['delete'], url_path='remove-inventory/(?P<requirement_id>[^/.]+)')
    def remove_inventory(self, request, pk=None, requirement_id=None):
        """Удалить требование по инвентарю"""
        task = self.get_object()
        try:
            req = task.inventory_requirements.get(id=requirement_id)
            req.delete()
            return Response({'status': 'ok'})
        except TaskInventoryRequirement.DoesNotExist:
            return Response({'error': 'Требование не найдено'}, status=404)