from django.contrib import admin
from .models import Counterparty, CounterpartyBankAccount


class CounterpartyBankAccountInline(admin.TabularInline):
    model = CounterpartyBankAccount
    extra = 1
    fields = ['bank', 'account_number', 'is_primary']


@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'phone', 'email', 'inn', 'created_at']
    search_fields = ['name', 'phone', 'email', 'inn', 'ogrn']
    list_filter = ['type']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'type', 'description')
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'telegram', 'whatsapp')
        }),
        ('Адреса', {
            'fields': ('legal_address', 'actual_address')
        }),
        ('Реквизиты', {
            'fields': ('inn', 'ogrn', 'kpp')
        }),
    )
    inlines = [CounterpartyBankAccountInline]