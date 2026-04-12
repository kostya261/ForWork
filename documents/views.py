from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import (
    MaterialRequest, MaterialRequestItem,
    InventoryIssue, InventoryIssueItem, WarehouseReceipt, WarehouseExpense, WarehouseTransfer, WarehouseStocktake,
    InventoryWriteOff, InventoryTransfer, InventoryStocktake, WorkOrder, CompletionAct, Invoice, InvoiceFactura
)
from .serializers import (
    MaterialRequestListSerializer, MaterialRequestDetailSerializer,
    MaterialRequestCreateSerializer, MaterialRequestUpdateStatusSerializer,
    IssueMaterialItemSerializer,
    InventoryIssueListSerializer, InventoryIssueDetailSerializer,
    InventoryIssueCreateSerializer, InventoryIssueUpdateStatusSerializer,
    ReturnInventoryItemSerializer, WarehouseReceiptSerializer, WarehouseReceiptCreateSerializer,
    WarehouseExpenseSerializer, WarehouseExpenseCreateSerializer, WarehouseTransferSerializer,
    WarehouseTransferCreateSerializer, WarehouseStocktakeSerializer, WarehouseStocktakeCreateSerializer,
    InventoryWriteOffSerializer, InventoryWriteOffCreateSerializer, InventoryTransferSerializer,
    InventoryTransferCreateSerializer, InventoryStocktakeSerializer, InventoryStocktakeCreateSerializer,
    WorkOrderCreateSerializer, WorkOrderSerializer, CompletionActCreateSerializer, CompletionActSerializer,
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceFacturaSerializer, InvoiceFacturaCreateSerializer
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


class WarehouseReceiptViewSet(viewsets.ModelViewSet):
    queryset = WarehouseReceipt.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return WarehouseReceiptCreateSerializer
        return WarehouseReceiptSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        """Провести накладную"""
        receipt = self.get_object()
        if receipt.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)

        receipt.status = 'conducted'
        receipt.conducted_by = request.user
        receipt.save()

        return Response(WarehouseReceiptSerializer(receipt).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить накладную"""
        receipt = self.get_object()
        if receipt.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённую накладную'}, status=400)

        receipt.status = 'cancelled'
        receipt.save()

        return Response(WarehouseReceiptSerializer(receipt).data)


class WarehouseExpenseViewSet(viewsets.ModelViewSet):
    queryset = WarehouseExpense.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return WarehouseExpenseCreateSerializer
        return WarehouseExpenseSerializer

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        expense = self.get_object()
        if expense.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)

        # Проверяем наличие на складе
        for item in expense.items.all():
            if item.warehouse_item.quantity < item.quantity:
                return Response({'error': f'Недостаточно {item.warehouse_item.name} на складе'}, status=400)

        expense.status = 'conducted'
        expense.conducted_by = request.user
        expense.save()
        return Response(WarehouseExpenseSerializer(expense).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        expense = self.get_object()
        if expense.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённую накладную'}, status=400)
        expense.status = 'cancelled'
        expense.save()
        return Response(WarehouseExpenseSerializer(expense).data)


class WarehouseTransferViewSet(viewsets.ModelViewSet):
    queryset = WarehouseTransfer.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return WarehouseTransferCreateSerializer
        return WarehouseTransferSerializer

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)

        # Проверяем наличие на складе-отправителе
        for item in transfer.items.all():
            if item.warehouse_item.quantity < item.quantity:
                return Response({'error': f'Недостаточно {item.warehouse_item.name} на складе-отправителе'}, status=400)

        transfer.status = 'conducted'
        transfer.conducted_by = request.user
        transfer.save()
        return Response(WarehouseTransferSerializer(transfer).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённое перемещение'}, status=400)
        transfer.status = 'cancelled'
        transfer.save()
        return Response(WarehouseTransferSerializer(transfer).data)


class WarehouseStocktakeViewSet(viewsets.ModelViewSet):
    queryset = WarehouseStocktake.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return WarehouseStocktakeCreateSerializer
        return WarehouseStocktakeSerializer

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        stocktake = self.get_object()
        if stocktake.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)

        stocktake.status = 'conducted'
        stocktake.conducted_by = request.user
        stocktake.save()
        return Response(WarehouseStocktakeSerializer(stocktake).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        stocktake = self.get_object()
        if stocktake.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённую инвентаризацию'}, status=400)
        stocktake.status = 'cancelled'
        stocktake.save()
        return Response(WarehouseStocktakeSerializer(stocktake).data)


class InventoryWriteOffViewSet(viewsets.ModelViewSet):
    queryset = InventoryWriteOff.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return InventoryWriteOffCreateSerializer
        return InventoryWriteOffSerializer

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        writeoff = self.get_object()
        if writeoff.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)
        writeoff.status = 'conducted'
        writeoff.conducted_by = request.user
        writeoff.save()
        return Response(InventoryWriteOffSerializer(writeoff).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        writeoff = self.get_object()
        if writeoff.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённое списание'}, status=400)
        writeoff.status = 'cancelled'
        writeoff.save()
        return Response(InventoryWriteOffSerializer(writeoff).data)


class InventoryTransferViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransfer.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return InventoryTransferCreateSerializer
        return InventoryTransferSerializer

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)
        transfer.status = 'conducted'
        transfer.conducted_by = request.user
        transfer.save()
        return Response(InventoryTransferSerializer(transfer).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённое перемещение'}, status=400)
        transfer.status = 'cancelled'
        transfer.save()
        return Response(InventoryTransferSerializer(transfer).data)


class InventoryStocktakeViewSet(viewsets.ModelViewSet):
    queryset = InventoryStocktake.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return InventoryStocktakeCreateSerializer
        return InventoryStocktakeSerializer

    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        stocktake = self.get_object()
        if stocktake.status != 'draft':
            return Response({'error': 'Можно провести только черновик'}, status=400)
        stocktake.status = 'conducted'
        stocktake.conducted_by = request.user
        stocktake.save()
        return Response(InventoryStocktakeSerializer(stocktake).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        stocktake = self.get_object()
        if stocktake.status == 'conducted':
            return Response({'error': 'Нельзя отменить проведённую инвентаризацию'}, status=400)
        stocktake.status = 'cancelled'
        stocktake.save()
        return Response(InventoryStocktakeSerializer(stocktake).data)


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        order = self.get_object()
        if order.status != 'draft':
            return Response({'error': 'Можно выдать только черновик'}, status=400)
        order.status = 'issued'
        order.issued_by = request.user
        order.save()
        return Response(WorkOrderSerializer(order).data)

    def get_serializer_class(self):
        return WorkOrderCreateSerializer if self.action=='create' else WorkOrderSerializer


class CompletionActViewSet(viewsets.ModelViewSet):
    queryset = CompletionAct.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return CompletionActCreateSerializer if self.action == 'create' else CompletionActSerializer

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        act = self.get_object()
        if act.status != 'draft':
            return Response({'error': 'Можно подписать только черновик'}, status=400)
        act.status = 'signed'
        act.signed_by = request.user
        act.save()
        return Response(CompletionActSerializer(act).data)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return InvoiceCreateSerializer if self.action == 'create' else InvoiceSerializer

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status != 'draft':
            return Response({'error': 'Можно отправить только черновик'}, status=400)
        invoice.status = 'sent'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status not in ['draft', 'sent']:
            return Response({'error': 'Нельзя отметить как оплаченный'}, status=400)
        invoice.status = 'paid'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status == 'paid':
            return Response({'error': 'Нельзя отменить оплаченный счёт'}, status=400)
        invoice.status = 'cancelled'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)


class InvoiceFacturaViewSet(viewsets.ModelViewSet):
    queryset = InvoiceFactura.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InvoiceFacturaCreateSerializer
        return InvoiceFacturaSerializer

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        factura = self.get_object()
        if factura.status != 'draft':
            return Response({'error': 'Можно выставить только черновик'}, status=400)
        factura.status = 'issued'
        factura.save()
        return Response(InvoiceFacturaSerializer(factura).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        factura = self.get_object()
        if factura.status == 'issued':
            return Response({'error': 'Нельзя отменить выставленный счёт-фактуру'}, status=400)
        factura.status = 'cancelled'
        factura.save()
        return Response(InvoiceFacturaSerializer(factura).data)