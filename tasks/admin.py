from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Task, TaskStatusHistory, TaskComment,
    TaskInventoryRequirement, TaskMaterialRequirement
)


class TaskStatusHistoryInline(admin.TabularInline):
    model = TaskStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'comment', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 1
    fields = ['author', 'text']


class TaskInventoryRequirementInline(admin.TabularInline):
    model = TaskInventoryRequirement
    extra = 1
    fields = ['inventory', 'quantity', 'comment']


class TaskMaterialRequirementInline(admin.TabularInline):
    model = TaskMaterialRequirement
    extra = 1
    fields = ['warehouse_item', 'planned_quantity', 'consumed_quantity', 'comment']
    readonly_fields = ['consumed_quantity']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'priority_colored', 'status_colored', 'responsible', 'department', 'deadline',
                    'created_at']
    list_filter = ['status', 'priority', 'department', 'created_at']
    search_fields = ['name', 'description', 'id']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description')
        }),
        ('Статус и срочность', {
            'fields': ('status', 'priority', 'deadline', 'completed_at')
        }),
        ('Ответственные', {
            'fields': ('created_by', 'responsible', 'co_executors')
        }),
        ('Связи', {
            'fields': ('counterparty', 'department')
        }),
    )
    filter_horizontal = ['co_executors']
    inlines = [
        TaskInventoryRequirementInline,
        TaskMaterialRequirementInline,
        TaskCommentInline,
        TaskStatusHistoryInline,
    ]
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'completed_at']

    def priority_colored(self, obj):
        colors = {
            'low': 'green',
            'medium': 'blue',
            'high': 'orange',
            'critical': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.priority, 'black'),
            obj.get_priority_display()
        )

    priority_colored.short_description = 'Срочность'
    priority_colored.admin_order_field = 'priority'

    def status_colored(self, obj):
        colors = {
            'new': 'gray',
            'assigned': 'blue',
            'in_progress': 'orange',
            'paused': 'purple',
            'completed': 'green',
            'closed': 'darkgreen',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    status_colored.short_description = 'Статус'
    status_colored.admin_order_field = 'status'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TaskComment) and not instance.pk:
                instance.author = request.user
            instance.save()
        formset.save_m2m()


@admin.register(TaskStatusHistory)
class TaskStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['task', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['task__name']
    readonly_fields = ['task', 'old_status', 'new_status', 'changed_by', 'comment', 'created_at']