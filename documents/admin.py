from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MaterialRequest, MaterialRequestItem,
    InventoryIssue, InventoryIssueItem
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