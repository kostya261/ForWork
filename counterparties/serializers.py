from rest_framework import serializers
from .models import Counterparty, CounterpartyBankAccount
from banks.serializers import BankSerializer


class CounterpartyBankAccountSerializer(serializers.ModelSerializer):
    bank_details = BankSerializer(source='bank', read_only=True)

    class Meta:
        model = CounterpartyBankAccount
        fields = [
            'id', 'bank', 'bank_details', 'account_number',
            'is_primary', 'created_at'
        ]
        read_only_fields = ['created_at']


class CounterpartyListSerializer(serializers.ModelSerializer):
    primary_account = serializers.SerializerMethodField()

    class Meta:
        model = Counterparty
        fields = [
            'id', 'name', 'type', 'phone', 'email',
            'inn', 'primary_account', 'created_at'
        ]

    def get_primary_account(self, obj):
        primary = obj.bank_accounts.filter(is_primary=True).first()
        if primary:
            return f"{primary.bank.name}: {primary.account_number}"
        return None


class CounterpartyDetailSerializer(serializers.ModelSerializer):
    bank_accounts = CounterpartyBankAccountSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Counterparty
        fields = [
            'id', 'name', 'type', 'description',
            'phone', 'email', 'telegram', 'whatsapp',
            'legal_address', 'actual_address',
            'inn', 'ogrn', 'kpp',
            'bank_accounts', 'tasks_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_tasks_count(self, obj):
        return obj.tasks.count()