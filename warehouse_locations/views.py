from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import WarehouseRack, WarehouseCell
from .serializers import (
    WarehouseRackSerializer, WarehouseRackCreateSerializer,
    WarehouseCellSerializer, WarehouseCellCreateSerializer, WarehouseCellListSerializer
)


class WarehouseRackViewSet(viewsets.ModelViewSet):
    queryset = WarehouseRack.objects.all().select_related('department').prefetch_related('cells')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return WarehouseRackCreateSerializer
        return WarehouseRackSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class WarehouseCellViewSet(viewsets.ModelViewSet):
    queryset = WarehouseCell.objects.all().select_related('rack', 'rack__department')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rack', 'rack__department']
    search_fields = ['name', 'number']
    ordering_fields = ['name', 'number', 'created_at']
    ordering = ['rack__name', 'number']

    def get_serializer_class(self):
        if self.action == 'list':
            return WarehouseCellListSerializer
        if self.action == 'create':
            return WarehouseCellCreateSerializer
        return WarehouseCellSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)