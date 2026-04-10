from django.contrib import admin
from .models import Bank


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'bik', 'correspondent_account', 'inn', 'phone']
    search_fields = ['name', 'short_name', 'bik', 'inn', 'ogrn', 'swift']
    list_filter = []
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_name', 'description')
        }),
        ('Банковские идентификаторы', {
            'fields': ('bik', 'swift', 'correspondent_account')
        }),
        ('Реквизиты юрлица', {
            'fields': ('inn', 'kpp', 'ogrn')
        }),
        ('Адреса и контакты', {
            'fields': ('legal_address', 'actual_address', 'phone', 'email', 'website')
        }),
    )