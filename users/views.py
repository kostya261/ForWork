from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import User
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserMeSerializer,
    PositionSerializer, DepartmentSerializer
)
from positions.models import Position
from departments.models import Department

User = get_user_model()


class PositionViewSet(viewsets.ModelViewSet):
    """CRUD для должностей"""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DepartmentViewSet(viewsets.ModelViewSet):
    """CRUD для отделов"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'description', 'legal_address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Получить всех пользователей отдела"""
        department = self.get_object()
        users = department.users.all()
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Получить инвентарь отдела"""
        department = self.get_object()
        inventory = department.inventory_items.all()
        from inventory.serializers import InventoryItemListSerializer
        serializer = InventoryItemListSerializer(inventory, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """CRUD для пользователей"""
    queryset = User.objects.all().select_related('position', 'department', 'photo')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['position', 'department', 'is_active', 'has_transport']
    search_fields = ['username', 'first_name', 'last_name', 'middle_name', 'email', 'phone']
    ordering_fields = ['username', 'last_name', 'date_joined', 'created_at']
    ordering = ['last_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'me':
            return UserMeSerializer
        return UserDetailSerializer

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Текущий авторизованный пользователь"""
        if request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Задачи, где пользователь ответственный"""
        user = self.get_object()
        tasks = user.responsible_tasks.all()
        from tasks.serializers import TaskListSerializer
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Инвентарь, за который отвечает пользователь"""
        user = self.get_object()
        inventory = user.responsible_inventory.all()
        from inventory.serializers import InventoryItemListSerializer
        serializer = InventoryItemListSerializer(inventory, many=True)
        return Response(serializer.data)