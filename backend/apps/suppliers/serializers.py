from rest_framework import serializers
from .models import (
    Supplier, SupplierContact, PurchaseOrder,
    PurchaseOrderItem, PurchaseOrderReceive, PurchaseOrderReceiveItem
)


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = ['id', 'name', 'title', 'phone', 'email', 'is_primary', 'notes']


class SupplierSerializer(serializers.ModelSerializer):
    contacts = SupplierContactSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'address', 'city', 'postal_code',
            'phone', 'email', 'website', 'description', 'tax_id',
            'assigned_to', 'is_active', 'created_at', 'updated_at',
            'contacts'
        ]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    variant_name = serializers.ReadOnlyField(source='variant.name', allow_null=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'product', 'product_name',
            'variant', 'variant_name', 'quantity_ordered',
            'quantity_received', 'unit_price', 'line_total',
            'is_fully_received'
        ]
        read_only_fields = ['line_total', 'quantity_received', 'is_fully_received']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    branch_name = serializers.ReadOnlyField(source='branch.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name', allow_null=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_name', 'branch',
            'branch_name', 'status', 'created_by', 'created_by_name',
            'approved_by', 'approved_by_name', 'order_date',
            'expected_delivery_date', 'created_at', 'updated_at',
            'subtotal', 'tax', 'shipping_cost', 'discount', 'total',
            'notes', 'supplier_reference', 'items'
        ]
        read_only_fields = ['po_number', 'total', 'created_at', 'updated_at']


class PurchaseOrderReceiveItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='po_item.product.name')

    class Meta:
        model = PurchaseOrderReceiveItem
        fields = ['id', 'receive', 'po_item', 'product_name', 'quantity', 'notes']


class PurchaseOrderReceiveSerializer(serializers.ModelSerializer):
    items = PurchaseOrderReceiveItemSerializer(many=True, read_only=True)
    po_number = serializers.ReadOnlyField(source='purchase_order.po_number')
    received_by_name = serializers.ReadOnlyField(source='received_by.get_full_name')

    class Meta:
        model = PurchaseOrderReceive
        fields = [
            'id', 'purchase_order', 'po_number', 'receive_date',
            'received_by', 'received_by_name', 'reference', 'notes',
            'created_at', 'items'
        ]
        read_only_fields = ['created_at']