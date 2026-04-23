from django.contrib import admin
from django.utils.html import format_html
from .models import WarehouseRack, WarehouseCell


class WarehouseCellInline(admin.TabularInline):
    model = WarehouseCell
    extra = 1
    fields = ['name', 'number', 'description']


@admin.register(WarehouseRack)
class WarehouseRackAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'department', 'cells_count', 'created_at']
    list_filter = ['department']
    search_fields = ['number', 'name', 'description']
    inlines = [WarehouseCellInline]
    filter_horizontal = ['images']
    fieldsets = (
        ('Основное', {'fields': ('department', 'name', 'number', 'description')}),
        ('Изображения', {'fields': ('images',)}),
        ('Служебное', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    def cells_count(self, obj):
        return obj.cells.count()

    cells_count.short_description = 'Ячеек'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WarehouseCell)
class WarehouseCellAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'rack', 'items_count', 'created_at']
    list_filter = ['rack__department', 'rack']
    search_fields = ['number', 'name', 'description']
    filter_horizontal = ['images']
    fieldsets = (
        ('Основное', {'fields': ('rack', 'name', 'number', 'description')}),
        ('Характеристики', {'fields': ('width', 'height', 'depth', 'max_weight')}),
        ('Изображения', {'fields': ('images',)}),
        ('Служебное', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    def items_count(self, obj):
        return obj.items.count()

    items_count.short_description = 'Товаров'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)