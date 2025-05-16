from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """
    Product category with hierarchical structure using MPTT
    """
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent category')
    )
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(_('image'), upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttribute(models.Model):
    """
    Product attributes like color, size, material, etc.
    """
    name = models.CharField(_('name'), max_length=100)
    display_name = models.CharField(_('display name'), max_length=100)

    class Meta:
        verbose_name = _('product attribute')
        verbose_name_plural = _('product attributes')

    def __str__(self):
        return self.display_name


class Product(models.Model):
    """
    Main product model
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(_('price'), max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name=_('category')
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('supplier')
    )
    sku = models.CharField(_('SKU'), max_length=50, unique=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_featured = models.BooleanField(_('featured'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    attributes = models.ManyToManyField(
        ProductAttribute,
        through='ProductAttributeValue',
        related_name='products',
        verbose_name=_('attributes')
    )

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def main_image(self):
        """Return the primary product image or first image"""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    @property
    def discount_percentage(self):
        """Calculate discount percentage if discount price is set"""
        if self.discount_price and self.price > 0:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return round(discount, 1)
        return 0

    @property
    def final_price(self):
        """Return the discount price if available, otherwise the regular price"""
        if self.discount_price:
            return self.discount_price
        return self.price


class ProductImage(models.Model):
    """
    Product images (multiple images per product)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product')
    )
    image = models.ImageField(_('image'), upload_to='products/')
    is_primary = models.BooleanField(_('primary image'), default=False)
    alt_text = models.CharField(_('alternative text'), max_length=255, blank=True)
    display_order = models.PositiveIntegerField(_('display order'), default=0)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        """Ensure only one primary image per product"""
        if self.is_primary:
            # Set all other images of this product as not primary
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    """
    Values for product attributes (e.g. Material: Wood, Color: Red)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values',
        verbose_name=_('product')
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_('attribute')
    )
    value = models.CharField(_('value'), max_length=255)

    class Meta:
        verbose_name = _('product attribute value')
        verbose_name_plural = _('product attribute values')
        unique_together = ('product', 'attribute')

    def __str__(self):
        return f"{self.attribute.display_name}: {self.value}"


class ProductVariant(models.Model):
    """
    Product variants (e.g. size S, color blue)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('product')
    )
    sku = models.CharField(_('SKU'), max_length=50, unique=True)
    price = models.DecimalField(
        _('price'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('product variant')
        verbose_name_plural = _('product variants')

    def __str__(self):
        attribute_values = [str(attr) for attr in self.attributes.all()]
        return f"{self.product.name} - {', '.join(attribute_values)}"

    @property
    def final_price(self):
        """Return the variant price or discount price if available, otherwise the product price"""
        if self.discount_price:
            return self.discount_price
        if self.price:
            return self.price
        return self.product.final_price


class VariantAttributeValue(models.Model):
    """
    Attributes for specific product variants (e.g. Size: XL, Color: Blue)
    """
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name=_('variant')
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='variant_values',
        verbose_name=_('attribute')
    )
    value = models.CharField(_('value'), max_length=255)

    class Meta:
        verbose_name = _('variant attribute value')
        verbose_name_plural = _('variant attribute values')
        unique_together = ('variant', 'attribute')

    def __str__(self):
        return f"{self.attribute.display_name}: {self.value}"


class ProductReview(models.Model):
    """
    Customer reviews and ratings for products
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('product')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name=_('user')
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=[(i, i) for i in range(1, 6)],
        help_text=_('Rating from 1 to 5')
    )
    comment = models.TextField(_('comment'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_approved = models.BooleanField(_('approved'), default=False)

    class Meta:
        verbose_name = _('product review')
        verbose_name_plural = _('product reviews')
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.get_full_name()}"


class Wishlist(models.Model):
    """
    User's wishlist
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist',
        verbose_name=_('user')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('wishlist')
        verbose_name_plural = _('wishlists')

    def __str__(self):
        return f"Wishlist for {self.user.get_full_name()}"


class WishlistItem(models.Model):
    """
    Items in user's wishlist
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('wishlist')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name=_('product')
    )
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)

    class Meta:
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        unique_together = ('wishlist', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.get_full_name()}'s wishlist"


class RecentlyViewed(models.Model):
    """
    Products recently viewed by users
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recently_viewed',
        verbose_name=_('user')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recently_viewed_by',
        verbose_name=_('product')
    )
    viewed_at = models.DateTimeField(_('viewed at'), auto_now=True)

    class Meta:
        verbose_name = _('recently viewed product')
        verbose_name_plural = _('recently viewed products')
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.product.name} viewed by {self.user.get_full_name()}"
