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

    # 🔥 СОЗДАНИЕ с банковскими счетами
    def create(self, validated_data):
        request = self.context.get('request')
        bank_accounts_data = request.data.get('bank_accounts', [])

        counterparty = Counterparty.objects.create(**validated_data)

        for acc_data in bank_accounts_data:
            CounterpartyBankAccount.objects.create(
                counterparty=counterparty,
                bank_id=acc_data.get('bank_id'),
                account_number=acc_data.get('account_number'),
                is_primary=acc_data.get('is_primary', False)
            )

        return counterparty

    # 🔥 ОБНОВЛЕНИЕ с банковскими счетами
    def update(self, instance, validated_data):
        request = self.context.get('request')
        bank_accounts_data = request.data.get('bank_accounts', None)

        # Обновляем основные поля
        instance.name = validated_data.get('name', instance.name)
        instance.type = validated_data.get('type', instance.type)
        instance.description = validated_data.get('description', instance.description)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.email = validated_data.get('email', instance.email)
        instance.telegram = validated_data.get('telegram', instance.telegram)
        instance.whatsapp = validated_data.get('whatsapp', instance.whatsapp)
        instance.legal_address = validated_data.get('legal_address', instance.legal_address)
        instance.actual_address = validated_data.get('actual_address', instance.actual_address)
        instance.inn = validated_data.get('inn', instance.inn)
        instance.kpp = validated_data.get('kpp', instance.kpp)
        instance.ogrn = validated_data.get('ogrn', instance.ogrn)
        instance.save()

        # Обновляем банковские счета, если они переданы
        if bank_accounts_data is not None:
            # Удаляем старые счета
            instance.bank_accounts.all().delete()
            # Создаём новые
            for acc_data in bank_accounts_data:
                CounterpartyBankAccount.objects.create(
                    counterparty=instance,
                    bank_id=acc_data.get('bank_id'),
                    account_number=acc_data.get('account_number'),
                    is_primary=acc_data.get('is_primary', False)
                )

        return instance