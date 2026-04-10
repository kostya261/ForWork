from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import WarehouseItem, WarehouseTransaction
from .serializers import (
    WarehouseItemListSerializer, WarehouseItemDetailSerializer,
    WarehouseTransactionSerializer, WarehouseTransactionCreateSerializer
)


class WarehouseItemViewSet(viewsets.ModelViewSet):
    queryset = WarehouseItem.objects.all().select_related(
        'category', 'manufacturer', 'department'
    ).prefetch_related('images', 'transactions')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'manufacturer', 'department', 'unit']
    search_fields = ['name', 'description', 'article', 'serial_number']
    ordering_fields = ['name', 'quantity', 'purchase_price', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return WarehouseItemListSerializer
        return WarehouseItemDetailSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Товары с низким остатком"""
        items = self.get_queryset()
        low_stock_items = [item for item in items if item.is_low_stock]
        serializer = WarehouseItemListSerializer(low_stock_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Все транзакции по товару"""
        item = self.get_object()
        transactions = item.transactions.all()
        serializer = WarehouseTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class WarehouseTransactionViewSet(viewsets.ModelViewSet):
    queryset = WarehouseTransaction.objects.all().select_related(
        'item', 'from_department', 'to_department', 'task', 'created_by'
    )
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['item', 'transaction_type', 'from_department', 'to_department', 'task']
    search_fields = ['comment', 'item__name']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WarehouseTransactionCreateSerializer
        return WarehouseTransactionSerializer