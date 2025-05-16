from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Branch, Stock, StockMovement
from apps.users.serializers import UserSerializer
from apps.products.serializers import ProductSerializer, ProductVariantSerializer


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for Branch model"""
    manager_detail = UserSerializer(source='manager', read_only=True)

    class Meta:
        model = Branch
        fields = (
            'id', 'name', 'address', 'city', 'phone', 'email',
            'is_active', 'created_at', 'updated_at', 'manager', 'manager_detail'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'manager': {'write_only': True}
        }


class BranchListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Branch listings"""

    class Meta:
        model = Branch
        fields = ('id', 'name', 'city', 'is_active')


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""
    branch_detail = BranchListSerializer(source='branch', read_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)
    variant_detail = ProductVariantSerializer(source='variant', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Stock
        fields = (
            'id', 'branch', 'branch_detail', 'product', 'product_detail',
            'variant', 'variant_detail', 'quantity', 'reorder_level',
            'last_restocked', 'is_low_stock'
        )
        read_only_fields = ('id', 'last_restocked')


class StockUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating stock quantities"""

    class Meta:
        model = Stock
        fields = ('quantity', 'reorder_level')


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for StockMovement model"""
    stock_detail = serializers.SerializerMethodField()
    performed_by_detail = UserSerializer(source='performed_by', read_only=True)
    target_branch_detail = BranchListSerializer(source='target_branch', read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            'id', 'stock', 'stock_detail', 'quantity', 'movement_type',
            'reference', 'notes', 'performed_by', 'performed_by_detail',
            'target_branch', 'target_branch_detail', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def get_stock_detail(self, obj):
        return {
            'product_name': str(obj.stock.product),
            'variant': str(obj.stock.variant) if obj.stock.variant else None,
            'branch_name': str(obj.stock.branch)
        }

    def validate(self, attrs):
        """
        Validate stock movement data:
        - TRANSFER type requires target_branch
        - Quantity must be positive for ADDITION and TRANSFER
        - REMOVAL can't reduce stock below zero
        """
        movement_type = attrs.get('movement_type')
        quantity = attrs.get('quantity')
        stock = attrs.get('stock')
        target_branch = attrs.get('target_branch')

        # Validate transfer target branch
        if movement_type == 'TRANSFER' and not target_branch:
            raise serializers.ValidationError({
                'target_branch': _('Target branch is required for transfer movements.')
            })

        # Validate quantity
        if movement_type in ['ADDITION', 'TRANSFER'] and quantity <= 0:
            raise serializers.ValidationError({
                'quantity': _('Quantity must be positive for addition and transfer movements.')
            })

        # Validate removals
        if movement_type == 'REMOVAL':
            if quantity <= 0:
                raise serializers.ValidationError({
                    'quantity': _('Quantity must be positive for removal.')
                })
            if stock and stock.quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': _(f'Not enough stock. Current quantity: {stock.quantity}')
                })

        return attrs

    def create(self, validated_data):
        """
        Create stock movement and update stock quantity
        """
        stock = validated_data.get('stock')
        quantity = validated_data.get('quantity')
        movement_type = validated_data.get('movement_type')

        # Update stock quantity based on movement type
        if movement_type == 'ADDITION':
            stock.quantity += quantity
        elif movement_type == 'REMOVAL':
            stock.quantity -= quantity
        elif movement_type == 'TRANSFER':
            stock.quantity -= quantity
        elif movement_type == 'ADJUSTMENT':
            # quantity is the new absolute value for adjustment
            # No need to update here as it's handled in the view
            pass

        stock.save()

        # Create the movement record
        return super().create(validated_data)
