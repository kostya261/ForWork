from django.contrib import admin
from .models import Manufacturer


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'website', 'created_at']
    search_fields = ['name', 'description', 'country']
    list_filter = ['country']