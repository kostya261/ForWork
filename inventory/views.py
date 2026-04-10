from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import InventoryItem
from .serializers import InventoryItemListSerializer, InventoryItemDetailSerializer


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all().select_related(
        'manufacturer', 'department', 'responsible'
    ).prefetch_related('images')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'manufacturer', 'department', 'responsible', 'category']
    search_fields = ['name', 'description', 'inventory_number', 'serial_number']
    ordering_fields = ['name', 'inventory_number', 'purchase_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return InventoryItemListSerializer
        return InventoryItemDetailSerializer