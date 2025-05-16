from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserShippingAddress


class UserShippingAddressInline(admin.TabularInline):
    model = UserShippingAddress
    extra = 0
    fields = ('recipient_name', 'phone', 'address', 'city', 'postal_code', 'is_default')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'branch', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'branch')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'phone', 'address', 'avatar')}),
        (_('Role & Branch'), {'fields': ('role', 'branch')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'password1', 'password2', 'role'),
        }),
    )

    inlines = [UserShippingAddressInline]


@admin.register(UserShippingAddress)
class UserShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'user', 'city', 'phone', 'is_default')
    list_filter = ('is_default', 'city')
    search_fields = ('recipient_name', 'user__email', 'user__full_name', 'address', 'city')
    list_select_related = ('user',)
