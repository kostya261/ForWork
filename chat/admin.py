from django.contrib import admin
from django.utils.html import format_html
from .models import ChatRoom, Message, UserChatStatus


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'text_preview', 'attachments_count', 'created_at', 'is_read']
    fields = ['sender', 'text_preview', 'attachments_count', 'is_read', 'created_at']
    can_delete = False

    def text_preview(self, obj):
        if obj.text:
            return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
        return '[Вложение]'

    text_preview.short_description = 'Текст'

    def attachments_count(self, obj):
        count = obj.attachments.count()
        return f"📎 {count}" if count > 0 else '-'

    attachments_count.short_description = 'Вложения'

    def has_add_permission(self, request, obj):
        return False


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'room_type', 'participants_count', 'messages_count', 'last_message_time',
                    'created_at']
    list_filter = ['room_type', 'created_at']
    search_fields = ['name', 'participants__username']
    filter_horizontal = ['participants']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'room_type', 'participants', 'created_by')
        }),
    )
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    inlines = [MessageInline]

    def participants_count(self, obj):
        return obj.participants.count()

    participants_count.short_description = 'Участников'

    def messages_count(self, obj):
        return obj.messages.count()

    messages_count.short_description = 'Сообщений'

    def last_message_time(self, obj):
        last_msg = obj.messages.last()
        return last_msg.created_at if last_msg else '-'

    last_message_time.short_description = 'Последнее сообщение'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

        # При создании добавляем создателя в участники
        if not change:
            obj.participants.add(request.user)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room_link', 'sender', 'content_preview', 'is_read', 'created_at']
    list_filter = ['room', 'is_read', 'created_at']
    search_fields = ['text', 'sender__username', 'room__name']
    filter_horizontal = ['attachments']
    readonly_fields = ['created_at', 'updated_at']

    def room_link(self, obj):
        url = f"/admin/chat/chatroom/{obj.room.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.room)

    room_link.short_description = 'Комната'

    def content_preview(self, obj):
        if obj.text:
            return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
        return f"[{obj.attachments.count()} вложений]"

    content_preview.short_description = 'Содержание'


@admin.register(UserChatStatus)
class UserChatStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_online_colored', 'last_activity']
    list_filter = ['is_online']
    search_fields = ['user__username']
    readonly_fields = ['last_activity']

    def is_online_colored(self, obj):
        color = 'green' if obj.is_online else 'red'
        icon = '🟢' if obj.is_online else '🔴'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, 'Онлайн' if obj.is_online else 'Офлайн'
        )

    is_online_colored.short_description = 'Статус'
    is_online_colored.admin_order_field = 'is_online'