from django.contrib import admin
from .models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_by', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        """Автоматически проставляем uploaded_by при сохранении"""
        if not obj.pk:  # Только при создании
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)