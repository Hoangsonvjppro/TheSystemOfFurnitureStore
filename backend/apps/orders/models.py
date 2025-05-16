from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import uuid


class Cart(models.Model):
    """
    Shopping cart model
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f"Cart for {self.user.full_name}"

    @property
    def total_items(self):
        """Get the total number of items in cart"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def subtotal(self):
        """Calculate the cart subtotal before discounts, shipping, etc."""
        return sum(item.line_total for item in self.items.all())


class CartItem(models.Model):
    """
    Individual items in a shopping cart
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('variant'),
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ['cart', 'product', 'variant']
        ordering = ['-added_at']

    def __str__(self):
        variant_str = f" - {self.variant}" if self.variant else ""
        return f"{self.product.name}{variant_str} ({self.quantity}) in {self.cart}"

    @property
    def unit_price(self):
        """
        Get the price of the item (from variant if it exists, otherwise from product)
        """
        if self.variant:
            return self.variant.final_price
        return self.product.final_price

    @property
    def line_total(self):
        """Calculate line total for this cart item"""
        return self.unit_price * self.quantity


class Order(models.Model):
    """
    Customer order model
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('CONFIRMED', _('Confirmed')),
        ('PROCESSING', _('Processing')),
        ('PACKED', _('Packed')),
        ('SHIPPED', _('Shipped')),
        ('DELIVERED', _('Delivered')),
        ('CANCELLED', _('Cancelled')),
        ('RETURNED', _('Returned')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('FAILED', _('Failed')),
        ('REFUNDED', _('Refunded')),
        ('PARTIALLY_REFUNDED', _('Partially Refunded')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', _('Credit Card')),
        ('DEBIT_CARD', _('Debit Card')),
        ('BANK_TRANSFER', _('Bank Transfer')),
        ('CASH_ON_DELIVERY', _('Cash on Delivery')),
        ('DIGITAL_WALLET', _('Digital Wallet')),
    ]

    order_number = models.CharField(_('order number'), max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('customer')
    )
    branch = models.ForeignKey(
        'inventory.Branch',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('branch')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH_ON_DELIVERY'
    )

    # Shipping information
    shipping_address = models.ForeignKey(
        'users.UserShippingAddress',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('shipping address')
    )
    shipping_name = models.CharField(_('recipient name'), max_length=100)
    shipping_phone = models.CharField(_('recipient phone'), max_length=20)
    shipping_address_line = models.TextField(_('address'))
    shipping_city = models.CharField(_('city'), max_length=100)
    shipping_postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    shipping_notes = models.TextField(_('shipping notes'), blank=True)

    # Financial information
    subtotal = models.DecimalField(_('subtotal'), max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(_('shipping cost'), max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(_('tax'), max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(_('discount'), max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(_('total'), max_digits=12, decimal_places=2)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), null=True, blank=True)
    shipped_at = models.DateTimeField(_('shipped at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)

    # Tracking
    tracking_number = models.CharField(_('tracking number'), max_length=100, blank=True)
    tracking_url = models.URLField(_('tracking URL'), blank=True)

    # Staff assignments
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_orders',
        verbose_name=_('processed by')
    )

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        # Generate unique order number if this is a new order
        if not self.order_number:
            self.order_number = self._generate_order_number()

        # Update status timestamps
        if self.status == 'CONFIRMED' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == 'SHIPPED' and not self.shipped_at:
            self.shipped_at = timezone.now()
        elif self.status == 'DELIVERED' and not self.delivered_at:
            self.delivered_at = timezone.now()
        elif self.status == 'CANCELLED' and not self.cancelled_at:
            self.cancelled_at = timezone.now()

        super().save(*args, **kwargs)

    def _generate_order_number(self):
        """Generate a unique order number based on time and UUID"""
        year = str(timezone.now().year)[2:]  # Last two digits of year
        month = str(timezone.now().month).zfill(2)
        day = str(timezone.now().day).zfill(2)
        unique = str(uuid.uuid4().int)[:8]
        return f"{year}{month}{day}{unique}"


class OrderItem(models.Model):
    """
    Items within an order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('variant')
    )
    product_name = models.CharField(_('product name'), max_length=255)
    variant_details = models.CharField(_('variant details'), max_length=255, blank=True)
    sku = models.CharField(_('SKU'), max_length=50)
    quantity = models.PositiveIntegerField(_('quantity'))
    unit_price = models.DecimalField(_('unit price'), max_digits=12, decimal_places=2)
    line_total = models.DecimalField(_('line total'), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
        ordering = ['id']

    def __str__(self):
        variant_str = f" - {self.variant_details}" if self.variant_details else ""
        return f"{self.product_name}{variant_str} ({self.quantity}) in Order #{self.order.order_number}"


class OrderTracking(models.Model):
    """
    Order status tracking and history
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='tracking_history',
        verbose_name=_('order')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Order.STATUS_CHOICES
    )
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    notes = models.TextField(_('notes'), blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_updates',
        verbose_name=_('performed by')
    )

    class Meta:
        verbose_name = _('order tracking')
        verbose_name_plural = _('order tracking')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"