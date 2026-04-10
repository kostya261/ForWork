from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import InventoryCategory


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    mptt_level_indent = 20