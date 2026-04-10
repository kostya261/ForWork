from django.contrib import admin
from .models import WarehouseItem, WarehouseTransaction


class WarehouseTransactionInline(admin.TabularInline):
    model = WarehouseTransaction
    extra = 0
    readonly_fields = ['created_by', 'created_at']
    fields = ['transaction_type', 'quantity', 'from_department', 'to_department', 'comment']


@admin.register(WarehouseItem)
class WarehouseItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'article', 'quantity', 'unit', 'category', 'department', 'is_low_stock']
    list_filter = ['category', 'department', 'manufacturer', 'unit']
    search_fields = ['name', 'article', 'serial_number', 'description']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'article', 'serial_number')
        }),
        ('Классификация', {
            'fields': ('category', 'manufacturer')
        }),
        ('Количество и цены', {
            'fields': ('quantity', 'unit', 'min_stock', 'purchase_price', 'retail_price')
        }),
        ('Принадлежность', {
            'fields': ('department',)
        }),
        ('Изображения', {
            'fields': ('images',)
        }),
    )
    filter_horizontal = ['images']
    inlines = [WarehouseTransactionInline]


@admin.register(WarehouseTransaction)
class WarehouseTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'transaction_type', 'quantity', 'from_department', 'to_department', 'created_by',
                    'created_at']
    list_filter = ['transaction_type', 'from_department', 'to_department', 'created_at']
    search_fields = ['item__name', 'comment']
    readonly_fields = ['created_by', 'created_at']

    def save_model(self, request, obj, form, change):
        """Автоматически проставляем created_by и обновляем остаток"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

        # TODO: Здесь будет логика автоматического изменения quantity в WarehouseItem