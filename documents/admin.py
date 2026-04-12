from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MaterialRequest, MaterialRequestItem,
    InventoryIssue, InventoryIssueItem, WarehouseReceipt, WarehouseReceiptItem, WarehouseExpense, WarehouseExpenseItem,
    WarehouseTransfer, WarehouseTransferItem, WarehouseStocktake, WarehouseStocktakeItem, InventoryWriteOff,
    InventoryWriteOffItem, InventoryTransfer, InventoryTransferItem, InventoryStocktake, InventoryStocktakeItem,
    CompletionAct, CompletionActMaterial, WorkOrder, WorkOrderInventory, WorkOrderMaterial
)


class MaterialRequestItemInline(admin.TabularInline):
    model = MaterialRequestItem
    extra = 1
    fields = ['warehouse_item', 'requested_quantity', 'issued_quantity', 'comment']


@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ['number', 'department', 'status_colored', 'task_link', 'requested_date', 'created_by']
    list_filter = ['status', 'department', 'requested_date']
    search_fields = ['number', 'task__name', 'comment']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {
            'fields': ('number', 'task', 'department', 'status', 'requested_date', 'issued_date')
        }),
        ('Кто участвовал', {
            'fields': ('created_by', 'approved_by', 'issued_by')
        }),
        ('Комментарий', {
            'fields': ('comment',)
        }),
    )
    inlines = [MaterialRequestItemInline]

    def status_colored(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'approved': 'blue',
            'issued': 'green',
            'partially_issued': 'lightgreen',
            'closed': 'darkgreen',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    status_colored.short_description = 'Статус'

    def task_link(self, obj):
        if obj.task:
            url = f"/admin/tasks/task/{obj.task.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.task)
        return '-'

    task_link.short_description = 'Задача'


class InventoryIssueItemInline(admin.TabularInline):
    model = InventoryIssueItem
    extra = 1
    fields = ['inventory_item', 'quantity', 'responsible', 'returned', 'comment']


@admin.register(InventoryIssue)
class InventoryIssueAdmin(admin.ModelAdmin):
    list_display = ['number', 'department', 'status_colored', 'task_link', 'issue_date', 'created_by']
    list_filter = ['status', 'department', 'issue_date']
    search_fields = ['number', 'task__name', 'comment']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {
            'fields': ('number', 'task', 'department', 'status', 'issue_date', 'return_date')
        }),
        ('Кто участвовал', {
            'fields': ('created_by', 'approved_by', 'issued_by')
        }),
        ('Комментарий', {
            'fields': ('comment',)
        }),
    )
    inlines = [InventoryIssueItemInline]

    def status_colored(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'approved': 'blue',
            'issued': 'green',
            'returned': 'purple',
            'closed': 'darkgreen',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    status_colored.short_description = 'Статус'

    def task_link(self, obj):
        if obj.task:
            url = f"/admin/tasks/task/{obj.task.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.task)
        return '-'

    task_link.short_description = 'Задача'


class WarehouseReceiptItemInline(admin.TabularInline):
    model = WarehouseReceiptItem
    extra = 1


@admin.register(WarehouseReceipt)
class WarehouseReceiptAdmin(admin.ModelAdmin):
    list_display = ['number', 'supplier', 'department', 'status_colored', 'receipt_date', 'created_by']
    list_filter = ['status', 'department', 'receipt_date']
    search_fields = ['number', 'supplier__name']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {
            'fields': ('number', 'supplier', 'department', 'status', 'receipt_date')
        }),
        ('Кто участвовал', {
            'fields': ('created_by', 'conducted_by')
        }),
        ('Комментарий', {
            'fields': ('comment',)
        }),
    )
    inlines = [WarehouseReceiptItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    status_colored.short_description = 'Статус'


class WarehouseExpenseItemInline(admin.TabularInline):
    model = WarehouseExpenseItem
    extra = 1


@admin.register(WarehouseExpense)
class WarehouseExpenseAdmin(admin.ModelAdmin):
    list_display = ['number', 'department', 'counterparty', 'status_colored', 'expense_date', 'created_by']
    list_filter = ['status', 'department', 'expense_date']
    search_fields = ['number', 'counterparty__name']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {'fields': ('number', 'department', 'counterparty', 'task', 'status', 'expense_date')}),
        ('Кто участвовал', {'fields': ('created_by', 'conducted_by')}),
        ('Комментарий', {'fields': ('comment',)}),
    )
    inlines = [WarehouseExpenseItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           colors.get(obj.status, 'black'), obj.get_status_display())

    status_colored.short_description = 'Статус'


class WarehouseTransferItemInline(admin.TabularInline):
    model = WarehouseTransferItem
    extra = 1


@admin.register(WarehouseTransfer)
class WarehouseTransferAdmin(admin.ModelAdmin):
    list_display = ['number', 'from_department', 'to_department', 'status_colored', 'transfer_date', 'created_by']
    list_filter = ['status', 'from_department', 'to_department', 'transfer_date']
    search_fields = ['number']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {'fields': ('number', 'from_department', 'to_department', 'status', 'transfer_date')}),
        ('Кто участвовал', {'fields': ('created_by', 'conducted_by')}),
        ('Комментарий', {'fields': ('comment',)}),
    )
    inlines = [WarehouseTransferItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           colors.get(obj.status, 'black'), obj.get_status_display())

    status_colored.short_description = 'Статус'


class WarehouseStocktakeItemInline(admin.TabularInline):
    model = WarehouseStocktakeItem
    extra = 1
    fields = ['warehouse_item', 'book_quantity', 'actual_quantity']


@admin.register(WarehouseStocktake)
class WarehouseStocktakeAdmin(admin.ModelAdmin):
    list_display = ['number', 'department', 'status_colored', 'stocktake_date', 'created_by']
    list_filter = ['status', 'department', 'stocktake_date']
    search_fields = ['number']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {'fields': ('number', 'department', 'status', 'stocktake_date')}),
        ('Кто участвовал', {'fields': ('created_by', 'conducted_by')}),
        ('Комментарий', {'fields': ('comment',)}),
    )
    inlines = [WarehouseStocktakeItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           colors.get(obj.status, 'black'), obj.get_status_display())

    status_colored.short_description = 'Статус'


class InventoryWriteOffItemInline(admin.TabularInline):
    model = InventoryWriteOffItem
    extra = 1


@admin.register(InventoryWriteOff)
class InventoryWriteOffAdmin(admin.ModelAdmin):
    list_display = ['number', 'department', 'status_colored', 'writeoff_date', 'created_by']
    list_filter = ['status', 'department', 'writeoff_date']
    search_fields = ['number', 'reason']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {'fields': ('number', 'department', 'status', 'writeoff_date', 'reason')}),
        ('Кто участвовал', {'fields': ('created_by', 'conducted_by')}),
        ('Комментарий', {'fields': ('comment',)}),
    )
    inlines = [InventoryWriteOffItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           colors.get(obj.status, 'black'), obj.get_status_display())

    status_colored.short_description = 'Статус'


class InventoryTransferItemInline(admin.TabularInline):
    model = InventoryTransferItem
    extra = 1


@admin.register(InventoryTransfer)
class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = ['number', 'from_department', 'to_department', 'status_colored', 'transfer_date', 'created_by']
    list_filter = ['status', 'from_department', 'to_department']
    search_fields = ['number']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {'fields': ('number', 'from_department', 'to_department', 'status', 'transfer_date')}),
        ('Кто участвовал', {'fields': ('created_by', 'conducted_by')}),
        ('Комментарий', {'fields': ('comment',)}),
    )
    inlines = [InventoryTransferItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           colors.get(obj.status, 'black'), obj.get_status_display())

    status_colored.short_description = 'Статус'


class InventoryStocktakeItemInline(admin.TabularInline):
    model = InventoryStocktakeItem
    extra = 1


@admin.register(InventoryStocktake)
class InventoryStocktakeAdmin(admin.ModelAdmin):
    list_display = ['number', 'department', 'status_colored', 'stocktake_date', 'created_by']
    list_filter = ['status', 'department']
    search_fields = ['number']
    readonly_fields = ['number', 'created_at', 'updated_at']
    fieldsets = (
        ('Основное', {'fields': ('number', 'department', 'status', 'stocktake_date')}),
        ('Кто участвовал', {'fields': ('created_by', 'conducted_by')}),
        ('Комментарий', {'fields': ('comment',)}),
    )
    inlines = [InventoryStocktakeItemInline]

    def status_colored(self, obj):
        colors = {'draft': 'gray', 'conducted': 'green', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           colors.get(obj.status, 'black'), obj.get_status_display())

    status_colored.short_description = 'Статус'


class WorkOrderMaterialInline(admin.TabularInline):
    model = WorkOrderMaterial
    extra = 1

class WorkOrderInventoryInline(admin.TabularInline):
    model = WorkOrderInventory
    extra = 1

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['number', 'task', 'status', 'issue_date', 'created_by']
    list_filter = ['status']
    search_fields = ['number', 'task__name']
    readonly_fields = ['number', 'created_at', 'updated_at']
    inlines = [WorkOrderMaterialInline, WorkOrderInventoryInline]


class CompletionActMaterialInline(admin.TabularInline):
    model = CompletionActMaterial
    extra = 1

@admin.register(CompletionAct)
class CompletionActAdmin(admin.ModelAdmin):
    list_display = ['number', 'task', 'status', 'completion_date', 'created_by']
    list_filter = ['status']
    search_fields = ['number', 'task__name']
    readonly_fields = ['number', 'created_at', 'updated_at']
    inlines = [CompletionActMaterialInline]
