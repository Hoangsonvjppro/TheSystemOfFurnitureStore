from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from .models import Cart, CartItem, Order, OrderItem, OrderTracking


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'unit_price', 'line_total')
    readonly_fields = ('unit_price', 'line_total')
    autocomplete_fields = ('product', 'variant')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'subtotal', 'updated_at')
    search_fields = ('user__email', 'user__full_name')
    list_select_related = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'subtotal', 'total_items')
    fields = ('user', 'subtotal', 'total_items', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    def subtotal(self, obj):
        return f"${obj.subtotal}"

    subtotal.short_description = _('Subtotal')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'variant_details', 'sku', 'quantity', 'unit_price', 'line_total')
    readonly_fields = ('product_name', 'variant_details', 'sku', 'unit_price', 'line_total')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 1
    fields = ('status', 'notes', 'performed_by', 'timestamp')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('performed_by',)
    ordering = ('-timestamp',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at', 'branch')
    search_fields = ('order_number', 'user__email', 'shipping_name', 'shipping_phone')
    readonly_fields = (
        'order_number', 'created_at', 'updated_at', 'confirmed_at',
        'shipped_at', 'delivered_at', 'cancelled_at'
    )
    list_select_related = ('user', 'branch')
    autocomplete_fields = ('user', 'branch', 'shipping_address', 'processed_by')

    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'branch')
        }),
        (_('Status'), {
            'fields': ('status', 'payment_status', 'payment_method')
        }),
        (_('Shipping information'), {
            'fields': (
                'shipping_address', 'shipping_name', 'shipping_phone',
                'shipping_address_line', 'shipping_city', 'shipping_postal_code',
                'shipping_notes'
            )
        }),
        (_('Financial information'), {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total')
        }),
        (_('Tracking'), {
            'fields': ('tracking_number', 'tracking_url', 'processed_by')
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at', 'updated_at', 'confirmed_at',
                'shipped_at', 'delivered_at', 'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )

    inlines = [OrderItemInline, OrderTrackingInline]

    def total_amount(self, obj):
        return f"${obj.total}"

    total_amount.short_description = _('Total')

    def save_model(self, request, obj, form, change):
        """
        Override save_model to add status tracking when status changes
        """
        if change and 'status' in form.changed_data:
            # Add an OrderTracking entry when status changes
            OrderTracking.objects.create(
                order=obj,
                status=obj.status,
                notes=f"Status changed to {obj.get_status_display()}",
                performed_by=request.user
            )
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to handle the status tracking when added via inline
        """
        instances = formset.save(commit=False)

        for instance in instances:
            if isinstance(instance, OrderTracking):
                # Set the performer to current user if not specified
                if not instance.performed_by:
                    instance.performed_by = request.user

                # Update the parent order's status
                parent_order = instance.order
                if parent_order.status != instance.status:
                    parent_order.status = instance.status
                    parent_order.save(update_fields=['status'])

            instance.save()

        # Also handle deletes
        for instance in formset.deleted_objects:
            instance.delete()

        formset.save_m2m()


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp', 'performed_by')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__order_number', 'notes')
    autocomplete_fields = ('order', 'performed_by')
    readonly_fields = ('timestamp',)
    list_select_related = ('order', 'performed_by') 