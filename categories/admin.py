from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Category


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    mptt_level_indent = 20