from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .models import (
    Category, Product, ProductImage, ProductAttribute,
    ProductAttributeValue, ProductVariant, VariantAttributeValue,
    ProductReview, Wishlist, WishlistItem, RecentlyViewed
)
from apps.users.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    parent_name = serializers.StringRelatedField(source='parent', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'parent', 'parent_name',
            'description', 'image', 'is_active', 'created_at',
            'updated_at', 'products_count'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_products_count(self, obj):
        return obj.products.count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Category listing"""
    parent_name = serializers.StringRelatedField(source='parent', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'parent', 'parent_name', 'is_active', 'products_count')

    def get_products_count(self, obj):
        return obj.products.count()


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Serializer for ProductAttribute model"""

    class Meta:
        model = ProductAttribute
        fields = ('id', 'name', 'display_name')
        read_only_fields = ('id',)


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for ProductAttributeValue model"""
    attribute_name = serializers.StringRelatedField(source='attribute', read_only=True)

    class Meta:
        model = ProductAttributeValue
        fields = ('id', 'attribute', 'attribute_name', 'value')
        read_only_fields = ('id',)


class VariantAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for VariantAttributeValue model"""
    attribute_name = serializers.StringRelatedField(source='attribute', read_only=True)

    class Meta:
        model = VariantAttributeValue
        fields = ('id', 'attribute', 'attribute_name', 'value')
        read_only_fields = ('id',)


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model"""

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', 'is_primary', 'alt_text', 'display_order')
        read_only_fields = ('id',)


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant model"""
    attributes = VariantAttributeValueSerializer(many=True, read_only=True)
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            'id', 'product', 'sku', 'price', 'discount_price',
            'is_active', 'final_price', 'attributes'
        )
        read_only_fields = ('id',)

    def validate_sku(self, value):
        """Validate SKU is unique"""
        if ProductVariant.objects.filter(sku=value).exists():
            if self.instance and self.instance.sku == value:
                return value
            raise serializers.ValidationError(_("A variant with this SKU already exists."))
        return value


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview model"""
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = ProductReview
        fields = (
            'id', 'product', 'user', 'user_detail', 'rating',
            'comment', 'created_at', 'is_approved'
        )
        read_only_fields = ('id', 'created_at', 'is_approved')


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    supplier_name = serializers.StringRelatedField(source='supplier', read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'price', 'discount_price',
            'category', 'category_name', 'supplier', 'supplier_name',
            'sku', 'is_active', 'is_featured', 'created_at', 'updated_at',
            'discount_percentage', 'final_price', 'attribute_values',
            'variants', 'images', 'reviews', 'average_rating'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_average_rating(self, obj):
        """Calculate average product rating"""
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return 0.0

    def validate_sku(self, value):
        """Validate SKU is unique"""
        if Product.objects.filter(sku=value).exists():
            if self.instance and self.instance.sku == value:
                return value
            raise serializers.ValidationError(_("A product with this SKU already exists."))
        return value

    def validate(self, attrs):
        """Validate price is greater than discount price"""
        price = attrs.get('price')
        discount_price = attrs.get('discount_price')

        if price and discount_price and discount_price >= price:
            raise serializers.ValidationError({
                'discount_price': _("Discount price must be less than regular price.")
            })

        return attrs


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Product listing"""
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'price', 'discount_price', 'category_name',
            'sku', 'is_active', 'is_featured', 'discount_percentage',
            'final_price', 'main_image', 'average_rating'
        )

    def get_main_image(self, obj):
        main_image = obj.main_image
        if main_image:
            return main_image.image.url
        return None

    def get_average_rating(self, obj):
        """Calculate average product rating"""
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return 0.0


class WishlistItemSerializer(serializers.ModelSerializer):
    """Serializer for WishlistItem model"""
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'wishlist', 'product', 'product_detail', 'added_at')
        read_only_fields = ('id', 'added_at')


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for Wishlist model"""
    items = WishlistItemSerializer(many=True, read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'user_detail', 'items', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class RecentlyViewedSerializer(serializers.ModelSerializer):
    """Serializer for RecentlyViewed model"""
    product_detail = ProductListSerializer(source='product', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = RecentlyViewed
        fields = ('id', 'user', 'user_detail', 'product', 'product_detail', 'viewed_at')
        read_only_fields = ('id', 'viewed_at')