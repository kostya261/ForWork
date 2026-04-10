from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import (
    MaterialRequest, MaterialRequestItem,
    InventoryIssue, InventoryIssueItem
)
from .serializers import (
    MaterialRequestListSerializer, MaterialRequestDetailSerializer,
    MaterialRequestCreateSerializer, MaterialRequestUpdateStatusSerializer,
    IssueMaterialItemSerializer,
    InventoryIssueListSerializer, InventoryIssueDetailSerializer,
    InventoryIssueCreateSerializer, InventoryIssueUpdateStatusSerializer,
    ReturnInventoryItemSerializer
)


class MaterialRequestViewSet(viewsets.ModelViewSet):
    queryset = MaterialRequest.objects.all().select_related(
        'task', 'department', 'created_by', 'approved_by', 'issued_by'
    ).prefetch_related('items__warehouse_item')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'department', 'task']
    search_fields = ['number', 'comment', 'task__name']
    ordering_fields = ['number', 'status', 'requested_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return MaterialRequestListSerializer
        if self.action == 'create':
            return MaterialRequestCreateSerializer
        if self.action == 'update_status':
            return MaterialRequestUpdateStatusSerializer
        if self.action == 'issue_item':
            return IssueMaterialItemSerializer
        return MaterialRequestDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Обычный пользователь видит только требования своего отдела
        if not user.is_staff and not user.is_superuser:
            if user.department:
                queryset = queryset.filter(department=user.department)

        return queryset

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Изменить статус требования"""
        material_request = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        old_status = material_request.status

        # Проверка прав
        if new_status == 'approved' and not request.user.has_perm('documents.can_approve_materialrequest'):
            return Response(
                {'error': 'Недостаточно прав для одобрения'},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_status == 'issued' and not request.user.has_perm('documents.can_issue_materialrequest'):
            return Response(
                {'error': 'Недостаточно прав для выдачи'},
                status=status.HTTP_403_FORBIDDEN
            )

        material_request.status = new_status

        if new_status == 'approved':
            material_request.approved_by = request.user
        elif new_status == 'issued':
            material_request.issued_by = request.user
            material_request.issued_date = timezone.now().date()

        material_request.save()

        return Response(MaterialRequestDetailSerializer(material_request).data)

    @action(detail=True, methods=['post'])
    def issue_item(self, request, pk=None):
        """Выдать конкретную позицию (частичная выдача)"""
        material_request = self.get_object()

        if material_request.status not in ['approved', 'partially_issued']:
            return Response(
                {'error': 'Требование должно быть одобрено'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_id = serializer.validated_data['item_id']
        quantity = serializer.validated_data['quantity']

        try:
            item = material_request.items.get(id=item_id)
        except MaterialRequestItem.DoesNotExist:
            return Response(
                {'error': 'Позиция не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем остаток
        if item.warehouse_item.quantity < quantity:
            return Response(
                {'error': f'Недостаточно на складе. Доступно: {item.warehouse_item.quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, не превышает ли выдачу
        if item.issued_quantity + quantity > item.requested_quantity:
            return Response(
                {
                    'error': f'Нельзя выдать больше запрошенного. Осталось выдать: {item.requested_quantity - item.issued_quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.issued_quantity += quantity
        item.save()

        # Обновляем статус требования
        all_issued = all(i.issued_quantity >= i.requested_quantity for i in material_request.items.all())
        if all_issued:
            material_request.status = 'issued'
            material_request.issued_by = request.user
            material_request.issued_date = timezone.now().date()
        else:
            material_request.status = 'partially_issued'
        material_request.save()

        # Создаём транзакцию на складе
        from warehouse.models import WarehouseTransaction
        WarehouseTransaction.objects.create(
            item=item.warehouse_item,
            transaction_type='out',
            quantity=quantity,
            from_department=material_request.department,
            task=material_request.task,
            comment=f'Выдано по требованию №{material_request.number}',
            created_by=request.user
        )

        # Уменьшаем остаток
        item.warehouse_item.quantity -= quantity
        item.warehouse_item.save()

        return Response(MaterialRequestDetailSerializer(material_request).data)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Требования, созданные текущим пользователем"""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = MaterialRequestListSerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryIssueViewSet(viewsets.ModelViewSet):
    queryset = InventoryIssue.objects.all().select_related(
        'task', 'department', 'created_by', 'approved_by', 'issued_by'
    ).prefetch_related('items__inventory_item', 'items__responsible')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'department', 'task']
    search_fields = ['number', 'comment', 'task__name']
    ordering_fields = ['number', 'status', 'issue_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return InventoryIssueListSerializer
        if self.action == 'create':
            return InventoryIssueCreateSerializer
        if self.action == 'update_status':
            return InventoryIssueUpdateStatusSerializer
        if self.action == 'return_item':
            return ReturnInventoryItemSerializer
        return InventoryIssueDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if not user.is_staff and not user.is_superuser:
            if user.department:
                queryset = queryset.filter(department=user.department)

        return queryset

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Изменить статус накладной"""
        issue = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        # Проверка прав
        if new_status == 'approved' and not request.user.has_perm('documents.can_approve_inventoryissue'):
            return Response(
                {'error': 'Недостаточно прав для одобрения'},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_status == 'issued' and not request.user.has_perm('documents.can_issue_inventoryissue'):
            return Response(
                {'error': 'Недостаточно прав для выдачи'},
                status=status.HTTP_403_FORBIDDEN
            )

        issue.status = new_status

        if new_status == 'approved':
            issue.approved_by = request.user
        elif new_status == 'issued':
            issue.issued_by = request.user

        issue.save()

        return Response(InventoryIssueDetailSerializer(issue).data)

    @action(detail=True, methods=['post'])
    def return_item(self, request, pk=None):
        """Отметить инвентарь как возвращённый"""
        issue = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_id = serializer.validated_data['item_id']
        comment = serializer.validated_data.get('comment', '')

        try:
            item = issue.items.get(id=item_id)
        except InventoryIssueItem.DoesNotExist:
            return Response(
                {'error': 'Позиция не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        item.returned = True
        item.comment = comment or item.comment
        item.save()

        # Обновляем статус инвентаря
        inv = item.inventory_item
        inv.status = 'active'
        inv.responsible = None
        inv.save()

        # Проверяем, всё ли возвращено
        all_returned = all(i.returned for i in issue.items.all())
        if all_returned:
            issue.status = 'returned'
            issue.return_date = timezone.now().date()
            issue.save()

        return Response(InventoryIssueDetailSerializer(issue).data)

    @action(detail=False, methods=['get'])
    def my_issues(self, request):
        """Накладные, созданные текущим пользователем"""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = InventoryIssueListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_inventory(self, request):
        """Инвентарь, выданный текущему пользователю"""
        items = InventoryIssueItem.objects.filter(
            responsible=request.user,
            returned=False
        ).select_related('issue', 'inventory_item')

        data = []
        for item in items:
            data.append({
                'issue_id': item.issue.id,
                'issue_number': item.issue.number,
                'inventory_id': item.inventory_item.id,
                'inventory_name': item.inventory_item.name,
                'inventory_number': item.inventory_item.inventory_number,
                'quantity': item.quantity,
                'issue_date': item.issue.issue_date,
            })

        return Response(data)