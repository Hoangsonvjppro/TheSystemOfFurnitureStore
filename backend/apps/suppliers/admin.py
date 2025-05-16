from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Supplier, SupplierContact, PurchaseOrder,
    PurchaseOrderItem, PurchaseOrderReceive, PurchaseOrderReceiveItem
)


class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 1
    fields = ('name', 'title', 'phone', 'email', 'is_primary')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'phone', 'email', 'is_active')
    list_filter = ('is_active', 'city')
    search_fields = ('name', 'code', 'email', 'phone', 'description')
    prepopulated_fields = {'code': ('name',)}
    autocomplete_fields = ('assigned_to',)
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        (_('Contact information'), {
            'fields': ('phone', 'email', 'website')
        }),
        (_('Address'), {
            'fields': ('address', 'city', 'postal_code')
        }),
        (_('Additional details'), {
            'fields': ('tax_id', 'assigned_to')
        }),
    )
    inlines = [SupplierContactInline]


@admin.register(SupplierContact)
class SupplierContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'title', 'phone', 'email', 'is_primary')
    list_filter = ('is_primary', 'supplier')
    search_fields = ('name', 'email', 'phone', 'supplier__name')
    autocomplete_fields = ('supplier',)
    list_select_related = ('supplier',)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('product', 'variant', 'quantity_ordered', 'quantity_received', 'unit_price', 'line_total')
    readonly_fields = ('quantity_received', 'line_total')
    autocomplete_fields = ('product', 'variant')


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'variant', 'quantity_ordered', 'quantity_received', 'unit_price',
                    'line_total')
    list_filter = ('purchase_order__status',)
    search_fields = ('purchase_order__po_number', 'product__name', 'variant__sku')
    autocomplete_fields = ('purchase_order', 'product', 'variant')
    readonly_fields = ('quantity_received', 'line_total')
    list_select_related = ('purchase_order', 'product', 'variant')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'branch', 'status', 'total', 'created_at')
    list_filter = ('status', 'branch', 'created_at')
    search_fields = ('po_number', 'supplier__name', 'supplier_reference')
    autocomplete_fields = ('supplier', 'branch', 'created_by', 'approved_by')
    readonly_fields = ('po_number', 'created_at', 'updated_at', 'total')
    list_select_related = ('supplier', 'branch', 'created_by', 'approved_by')

    fieldsets = (
        (None, {
            'fields': ('po_number', 'supplier', 'branch', 'status')
        }),
        (_('Dates'), {
            'fields': ('order_date', 'expected_delivery_date', 'created_at', 'updated_at')
        }),
        (_('Financial'), {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'discount', 'total')
        }),
        (_('Additional info'), {
            'fields': ('notes', 'supplier_reference')
        }),
        (_('Personnel'), {
            'fields': ('created_by', 'approved_by')
        }),
    )

    inlines = [PurchaseOrderItemInline]

    def save_model(self, request, obj, form, change):
        if not change:  # Creating a new purchase order
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class PurchaseOrderReceiveItemInline(admin.TabularInline):
    model = PurchaseOrderReceiveItem
    extra = 1
    autocomplete_fields = ('po_item',)


@admin.register(PurchaseOrderReceive)
class PurchaseOrderReceiveAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'receive_date', 'received_by', 'reference')
    list_filter = ('receive_date',)
    search_fields = ('purchase_order__po_number', 'reference', 'notes')
    autocomplete_fields = ('purchase_order', 'received_by')
    list_select_related = ('purchase_order', 'purchase_order__supplier', 'received_by')

    fieldsets = (
        (None, {
            'fields': ('purchase_order', 'receive_date', 'received_by')
        }),
        (_('Details'), {
            'fields': ('reference', 'notes')
        }),
    )

    inlines = [PurchaseOrderReceiveItemInline]

    def save_model(self, request, obj, form, change):
        if not change:  # Creating a new receive record
            obj.received_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PurchaseOrderReceiveItem)
class PurchaseOrderReceiveItemAdmin(admin.ModelAdmin):
    list_display = ('receive', 'po_item', 'quantity')
    list_filter = ('receive',)
    search_fields = ('receive__purchase_order__po_number', 'po_item__product__name')
    autocomplete_fields = ('receive', 'po_item')
    list_select_related = ('receive', 'po_item', 'po_item__product')