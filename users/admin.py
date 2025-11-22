from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_manager', 'is_w_staff', 'is_superuser', 'date_joined')
    list_filter = ('is_manager', 'is_w_staff', 'is_superuser', 'is_active')
    
    # Override fieldsets to include custom fields
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('StockMaster Roles', {
            'fields': ('is_manager', 'is_w_staff'),
            'description': 'is_manager: Inventory Manager | is_w_staff: Warehouse Staff'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_manager', 'is_w_staff'),
        }),
    )
