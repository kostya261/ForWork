from rest_framework import viewsets, permissions
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

    def get_serializer_class(self):
        if self.action == 'list':
            return WarehouseCellListSerializer
        if self.action == 'create':
            return WarehouseCellCreateSerializer
        return WarehouseCellSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)