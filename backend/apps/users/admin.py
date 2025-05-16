from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserShippingAddress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'full_name', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'full_name', 'phone', 'address', 'avatar')}),
        (_('Role'), {'fields': ('role', 'branch')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(UserShippingAddress)
class UserShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient_name', 'city', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('user__email', 'user__full_name', 'recipient_name', 'address', 'city')
    raw_id_fields = ('user',)

    fieldsets = (
        (None, {'fields': ('user', 'is_default')}),
        (_('Recipient info'), {'fields': ('recipient_name', 'phone')}),
        (_('Address info'), {'fields': ('address', 'city', 'postal_code')}),
    )
