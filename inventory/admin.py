from django.contrib import admin
from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'inventory_number', 'serial_number', 'status', 'department', 'responsible']
    list_filter = ['status', 'department', 'manufacturer', 'category']
    search_fields = ['name', 'inventory_number', 'serial_number', 'description']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'manufacturer', 'category')
        }),
        ('Учетные данные', {
            'fields': ('serial_number', 'inventory_number', 'status')
        }),
        ('Даты', {
            'fields': ('production_date', 'purchase_date', 'receipt_date', 'decommission_date')
        }),
        ('Стоимость и списание', {
            'fields': ('purchase_price', 'decommission_reason')
        }),
        ('Принадлежность', {
            'fields': ('department', 'responsible')
        }),
        ('Изображения', {
            'fields': ('images',)
        }),
    )
    filter_horizontal = ['images']