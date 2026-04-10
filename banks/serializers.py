from rest_framework import serializers
from .models import Bank


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = [
            'id', 'name', 'short_name', 'bik', 'swift',
            'correspondent_account', 'inn', 'kpp', 'ogrn',
            'legal_address', 'phone', 'email', 'website'
        ]