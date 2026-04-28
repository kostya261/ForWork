from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'head', 'inn', 'created_at']
    search_fields = ['name', 'legal_address', 'actual_address', 'inn', 'kpp', 'ogrn', 'bank_account']
    list_filter = ['parent']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'parent', 'head')
        }),
        ('Адреса', {
            'fields': ('legal_address', 'actual_address')
        }),
        ('Реквизиты', {
            'fields': ('inn', 'kpp', 'ogrn')
        }),
        ('Банковские реквизиты', {
            'fields': ('bank', 'bank_account')
        }),
    )