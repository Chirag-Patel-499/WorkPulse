from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Company, Team


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company')
    list_filter = ('company',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        'username',
        'company',
        'team',
        'role',
        'is_active',
    )

    list_filter = (
        'company',
        'team',
        'role',
        'is_active',
    )

    fieldsets = (
        (None, {
            'fields': (
                'username',
                'password'
            )
        }),

        ('Company Info', {
            'fields': (
                'company',
                'team',
                'role'
            )
        }),

        ('Personal Info', {
            'fields': (
                'email',
                'first_name',
                'last_name'
            )
        }),

        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
    )

    search_fields = ('username',)
    ordering = ('username',)