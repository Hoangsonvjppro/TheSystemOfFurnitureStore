from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from django.utils.html import format_html

from .models import Branch, Stock, StockMovement


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'manager', 'is_active', 'phone', 'staff_count')
    list_filter = ('is_active', 'city')
    search_fields = ('name', 'address', 'city', 'email', 'phone')
    autocomplete_fields = ('manager',)

    def staff_count(self, obj):
        return obj.users.count()

    staff_count.short_description = _('Staff count')


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    fields = ('movement_type', 'quantity', 'performed_by', 'created_at', 'notes')
    readonly_fields = ('movement_type', 'quantity', 'performed_by', 'created_at')
    ordering = ('-created_at',)
    max_num = 10
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant_display', 'branch', 'quantity', 'stock_status', 'last_restocked')
    list_filter = ('branch', 'last_restocked')
    search_fields = ('product__name', 'product__sku', 'variant__sku', 'branch__name')
    autocomplete_fields = ('product', 'variant', 'branch')
    readonly_fields = ('last_restocked',)
    list_select_related = ('product', 'variant', 'branch')
    fieldsets = (
        (None, {
            'fields': ('branch', 'product', 'variant')
        }),
        (_('Stock levels'), {
            'fields': ('quantity', 'reorder_level', 'last_restocked')
        }),
    )
    inlines = [StockMovementInline]

    def variant_display(self, obj):
        if obj.variant:
            return obj.variant
        return '-'

    variant_display.short_description = _('Variant')

    def stock_status(self, obj):
        if obj.quantity <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange; font-weight: bold;">Low stock</span>')
        else:
            return format_html('<span style="color: green;">In stock</span>')

    stock_status.short_description = _('Status')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('movement_type', 'stock', 'quantity', 'reference', 'created_at', 'performed_by')
    list_filter = ('movement_type', 'created_at', 'stock__branch')
    search_fields = ('stock__product__name', 'stock__product__sku', 'reference', 'notes')
    autocomplete_fields = ('stock', 'performed_by', 'target_branch')
    readonly_fields = ('created_at',)
    list_select_related = ('stock', 'stock__product', 'stock__branch', 'performed_by')
    fieldsets = (
        (None, {
            'fields': ('stock', 'movement_type', 'quantity')
        }),
        (_('Reference'), {
            'fields': ('reference', 'notes')
        }),
        (_('Transfer details'), {
            'fields': ('target_branch',),
            'classes': ('collapse',),
        }),
        (_('Tracking'), {
            'fields': ('performed_by', 'created_at')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """Only show target_branch for transfers"""
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.movement_type != 'TRANSFER':
            # Remove the transfer details fieldset
            return [fs for fs in fieldsets if fs[0] != _('Transfer details')]
        return fieldsets 