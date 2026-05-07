from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff') # Only include fields that exist in our custom User model
    fieldsets = (
        (None, {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff')}),
    )
    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = () # Remove groups and user_permissions