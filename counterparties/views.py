from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Counterparty, CounterpartyBankAccount
from .serializers import (
    CounterpartyListSerializer, CounterpartyDetailSerializer,
    CounterpartyBankAccountSerializer
)


class CounterpartyViewSet(viewsets.ModelViewSet):
    queryset = Counterparty.objects.all().prefetch_related('bank_accounts__bank')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type']
    search_fields = ['name', 'phone', 'email', 'inn', 'ogrn']
    ordering_fields = ['name', 'type', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return CounterpartyListSerializer
        return CounterpartyDetailSerializer


class CounterpartyBankAccountViewSet(viewsets.ModelViewSet):
    queryset = CounterpartyBankAccount.objects.all().select_related('counterparty', 'bank')
    serializer_class = CounterpartyBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['counterparty', 'bank', 'is_primary']
    search_fields = ['account_number', 'counterparty__name', 'bank__name']
    ordering = ['counterparty__name', '-is_primary']