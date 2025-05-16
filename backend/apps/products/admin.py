from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from mptt.admin import MPTTModelAdmin

from .models import (
    Category, Product, ProductImage, ProductAttribute,
    ProductAttributeValue, ProductVariant, VariantAttributeValue,
    ProductReview, Wishlist, WishlistItem, RecentlyViewed
)


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'products_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def products_count(self, obj):
        return obj.products.count()

    products_count.short_description = _('Products')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_primary', 'alt_text', 'display_order')


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    autocomplete_fields = ('attribute',)


class VariantAttributeValueInline(admin.TabularInline):
    model = VariantAttributeValue
    extra = 1
    autocomplete_fields = ('attribute',)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('sku', 'price', 'discount_price', 'is_active')
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'price', 'discount_price', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'supplier')
    readonly_fields = ('created_at', 'updated_at', 'display_main_image')
    list_editable = ('is_active', 'is_featured')

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Categorization'), {
            'fields': ('category', 'supplier')
        }),
        (_('Pricing'), {
            'fields': ('price', 'discount_price')
        }),
        (_('Status'), {
            'fields': ('sku', 'is_active', 'is_featured')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
        (_('Preview'), {
            'fields': ('display_main_image',)
        }),
    )

    inlines = [
        ProductAttributeValueInline,
        ProductImageInline,
        ProductVariantInline,
    ]

    def display_main_image(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="150" height="150" />', obj.main_image.image.url)
        return _('No image')

    display_main_image.short_description = _('Main image')

    def discount_percentage(self, obj):
        if obj.discount_percentage:
            return f"{obj.discount_percentage}%"
        return "-"

    discount_percentage.short_description = _('Discount %')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'price', 'discount_price', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('sku', 'product__name')
    autocomplete_fields = ('product',)

    inlines = [VariantAttributeValueInline]


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name')
    search_fields = ('name', 'display_name')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    autocomplete_fields = ('product', 'user')
    list_editable = ('is_approved',)
    list_select_related = ('product', 'user')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'items_count', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    list_select_related = ('user',)

    def items_count(self, obj):
        return obj.items.count()

    items_count.short_description = _('Items')


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 1
    autocomplete_fields = ('product',)


admin.site.register(RecentlyViewed)