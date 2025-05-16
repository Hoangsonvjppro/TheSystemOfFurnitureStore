from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Branch(models.Model):
    """
    Store branch/location model
    """
    name = models.CharField(_('name'), max_length=100)
    address = models.TextField(_('address'))
    city = models.CharField(_('city'), max_length=100)
    phone = models.CharField(_('phone'), max_length=20)
    email = models.EmailField(_('email'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branch',
        verbose_name=_('manager'),
        limit_choices_to={'role': 'MANAGER'}
    )

    class Meta:
        verbose_name = _('branch')
        verbose_name_plural = _('branches')
        ordering = ['name']

    def __str__(self):
        return self.name


class Stock(models.Model):
    """
    Product inventory at specific branches
    """
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_('branch')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_('variant'),
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(_('quantity'), default=0)
    reorder_level = models.PositiveIntegerField(_('reorder level'), default=5)
    last_restocked = models.DateTimeField(_('last restocked'), auto_now_add=True)

    class Meta:
        verbose_name = _('stock')
        verbose_name_plural = _('stocks')
        unique_together = [['branch', 'product', 'variant']]
        ordering = ['branch', 'product']

    def __str__(self):
        variant_str = f" - {self.variant}" if self.variant else ""
        return f"{self.product}{variant_str} at {self.branch}"

    @property
    def is_low_stock(self):
        """Check if the stock is below reorder level"""
        return self.quantity <= self.reorder_level


class StockMovement(models.Model):
    """
    Stock movement tracking (additions, removals, transfers)
    """
    MOVEMENT_TYPES = [
        ('ADDITION', _('Addition')),
        ('REMOVAL', _('Removal')),
        ('TRANSFER', _('Transfer')),
        ('ADJUSTMENT', _('Adjustment')),
    ]

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name=_('stock')
    )
    quantity = models.IntegerField(_('quantity'))
    movement_type = models.CharField(
        _('movement type'),
        max_length=20,
        choices=MOVEMENT_TYPES
    )
    reference = models.CharField(_('reference'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        verbose_name=_('performed by')
    )
    target_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transfers',
        verbose_name=_('target branch')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('stock movement')
        verbose_name_plural = _('stock movements')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} of {self.quantity} {self.stock.product} at {self.stock.branch}"