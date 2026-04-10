from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Расширенная админка для кастомной модели User.
    """
    # Поля, которые показываем в списке пользователей
    list_display = [
        'username',
        'email',
        'last_name',
        'first_name',
        'middle_name',
        'position',
        'department',
        'is_active',
        'is_staff'
    ]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'position', 'department']
    search_fields = ['username', 'email', 'last_name', 'first_name', 'middle_name', 'phone']

    # Группировка полей в форме редактирования
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': (
                'middle_name', 'phone', 'telegram', 'whatsapp',
                'position', 'department',
                'passport_series', 'passport_number',
                'passport_issued_by', 'passport_issued_date',
                'has_transport', 'transport_description',
                'photo',
                'comment',
            )
        }),
    )

    # Поля при создании нового пользователя
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': (
                'middle_name', 'email', 'phone',
                'position', 'department',
            )
        }),
    )