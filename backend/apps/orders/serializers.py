from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem, OrderTracking
from apps.products.models import Product, ProductVariant
from apps.products.serializers import ProductSerializer, ProductVariantSerializer
from apps.users.serializers import UserSerializer, UserShippingAddressSerializer
from apps.inventory.models import Branch
from apps.inventory.serializers import BranchListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product_detail = ProductSerializer(source='product', read_only=True)
    variant_detail = ProductVariantSerializer(source='variant', read_only=True)
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    line_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_detail', 'variant',
            'variant_detail', 'quantity', 'unit_price',
            'line_total', 'added_at', 'updated_at'
        )
        read_only_fields = ('id', 'added_at', 'updated_at')

    def validate(self, attrs):
        """Validate cart item data"""
        product = attrs.get('product')
        variant = attrs.get('variant')
        quantity = attrs.get('quantity', 1)

        # Check if variant belongs to product
        if variant and variant.product != product:
            raise serializers.ValidationError({
                'variant': _('Variant does not belong to this product.')
            })

        # Check quantity
        if quantity <= 0:
            raise serializers.ValidationError({
                'quantity': _('Quantity must be greater than zero.')
            })

        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Cart
        fields = (
            'id', 'user', 'user_detail', 'items', 'total_items',
            'subtotal', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        required=False,
        allow_null=True
    )
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        """Validate cart data"""
        product = attrs.get('product')
        variant = attrs.get('variant')

        # Check if variant belongs to product
        if variant and variant.product != product:
            raise serializers.ValidationError({
                'variant': _('Variant does not belong to this product.')
            })

        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    product_detail = ProductSerializer(source='product', read_only=True)
    variant_detail = ProductVariantSerializer(source='variant', read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            'id', 'product', 'product_detail', 'variant', 'variant_detail',
            'product_name', 'variant_details', 'sku', 'quantity',
            'unit_price', 'line_total'
        )
        read_only_fields = fields


class OrderTrackingSerializer(serializers.ModelSerializer):
    """Serializer for order tracking history"""
    performed_by_detail = UserSerializer(source='performed_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderTracking
        fields = (
            'id', 'status', 'status_display', 'timestamp',
            'notes', 'performed_by', 'performed_by_detail'
        )
        read_only_fields = ('id', 'timestamp')


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    items = OrderItemSerializer(many=True, read_only=True)
    tracking_history = OrderTrackingSerializer(many=True, read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    branch_detail = BranchListSerializer(source='branch', read_only=True)
    shipping_address_detail = UserShippingAddressSerializer(
        source='shipping_address',
        read_only=True
    )
    processed_by_detail = UserSerializer(source='processed_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(
        source='get_payment_status_display',
        read_only=True
    )
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'user', 'user_detail', 'branch',
            'branch_detail', 'status', 'status_display', 'payment_status',
            'payment_status_display', 'payment_method', 'payment_method_display',
            'shipping_address', 'shipping_address_detail', 'shipping_name',
            'shipping_phone', 'shipping_address_line', 'shipping_city',
            'shipping_postal_code', 'shipping_notes', 'subtotal',
            'shipping_cost', 'tax', 'discount', 'total', 'created_at',
            'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at',
            'cancelled_at', 'tracking_number', 'tracking_url',
            'processed_by', 'processed_by_detail', 'items', 'tracking_history'
        )
        read_only_fields = (
            'id', 'order_number', 'created_at', 'updated_at',
            'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at'
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    shipping_address_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = (
            'branch', 'payment_method', 'shipping_address_id',
            'shipping_notes', 'shipping_cost'
        )

    def validate(self, attrs):
        user = self.context['request'].user
        shipping_address_id = attrs.pop('shipping_address_id', None)

        # Validate shipping address belongs to user
        if shipping_address_id:
            try:
                shipping_address = user.shipping_addresses.get(id=shipping_address_id)
                attrs['shipping_address'] = shipping_address
                attrs['shipping_name'] = shipping_address.recipient_name
                attrs['shipping_phone'] = shipping_address.phone
                attrs['shipping_address_line'] = shipping_address.address
                attrs['shipping_city'] = shipping_address.city
                attrs['shipping_postal_code'] = shipping_address.postal_code
            except:
                raise serializers.ValidationError({
                    'shipping_address_id': _('Invalid shipping address.')
                })

        # Get user's cart
        try:
            cart = user.cart
            if not cart.items.exists():
                raise serializers.ValidationError({
                    'non_field_errors': _('Your cart is empty.')
                })

            # Calculate order totals
            attrs['user'] = user
            attrs['subtotal'] = cart.subtotal
            attrs['tax'] = 0  # Calculate tax if needed
            attrs['discount'] = 0  # Apply discounts if any
            shipping_cost = attrs.get('shipping_cost', 0)
            attrs['total'] = cart.subtotal + shipping_cost

        except:
            raise serializers.ValidationError({
                'non_field_errors': _('User has no cart.')
            })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create order from cart"""
        user = validated_data['user']
        cart = user.cart

        # Create order
        order = Order.objects.create(**validated_data)

        # Create order items from cart items
        for cart_item in cart.items.select_related('product', 'variant'):
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_details=str(cart_item.variant) if cart_item.variant else '',
                sku=cart_item.variant.sku if cart_item.variant else cart_item.product.sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                line_total=cart_item.line_total
            )

        # Create initial order tracking
        OrderTracking.objects.create(
            order=order,
            status='PENDING',
            notes=_('Order placed'),
            performed_by=user
        )

        # Clear cart
        cart.items.all().delete()

        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status"""
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = ('status', 'notes')

    def validate(self, attrs):
        current_status = self.instance.status
        new_status = attrs.get('status')

        # Validate status transition
        valid_transitions = {
            'PENDING': ['CONFIRMED', 'CANCELLED'],
            'CONFIRMED': ['PROCESSING', 'CANCELLED'],
            'PROCESSING': ['PACKED', 'CANCELLED'],
            'PACKED': ['SHIPPED', 'CANCELLED'],
            'SHIPPED': ['DELIVERED', 'RETURNED'],
            'DELIVERED': ['RETURNED'],
            'CANCELLED': [],
            'RETURNED': []
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError({
                'status': _(f'Cannot change status from {current_status} to {new_status}')
            })

        return attrs

    def update(self, instance, validated_data):
        notes = validated_data.pop('notes', '')
        status = validated_data.get('status')
        user = self.context['request'].user

        # Update order
        order = super().update(instance, validated_data)

        # Create tracking record
        OrderTracking.objects.create(
            order=order,
            status=status,
            notes=notes or f"Status changed to {order.get_status_display()}",
            performed_by=user
        )

        return order


class OrderPaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payment status"""

    class Meta:
        model = Order
        fields = ('payment_status', 'payment_method')

    def update(self, instance, validated_data):
        user = self.context['request'].user
        old_status = instance.payment_status

        # Update order
        order = super().update(instance, validated_data)

        # Create tracking note for payment status change
        if 'payment_status' in validated_data and old_status != order.payment_status:
            OrderTracking.objects.create(
                order=order,
                status=order.status,
                notes=f"Payment status changed to {order.get_payment_status_display()}",
                performed_by=user
            )

        return order
