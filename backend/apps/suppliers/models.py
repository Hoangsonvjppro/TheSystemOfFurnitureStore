from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import uuid


class Supplier(models.Model):
    """
    Furniture suppliers/vendors model
    """
    name = models.CharField(_('name'), max_length=100)
    code = models.CharField(_('code'), max_length=20, unique=True)
    address = models.TextField(_('address'))
    city = models.CharField(_('city'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    phone = models.CharField(_('phone'), max_length=20)
    email = models.EmailField(_('email'), blank=True)
    website = models.URLField(_('website'), blank=True)
    description = models.TextField(_('description'), blank=True)
    tax_id = models.CharField(_('tax ID'), max_length=50, blank=True)

    # Relationship fields
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_suppliers',
        verbose_name=_('account manager')
    )

    # Status fields
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class SupplierContact(models.Model):
    """
    Contact persons for suppliers
    """
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('supplier')
    )
    name = models.CharField(_('name'), max_length=100)
    title = models.CharField(_('title'), max_length=100, blank=True)
    phone = models.CharField(_('phone'), max_length=20)
    email = models.EmailField(_('email'), blank=True)
    is_primary = models.BooleanField(_('primary contact'), default=False)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('supplier contact')
        verbose_name_plural = _('supplier contacts')
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"

    def save(self, *args, **kwargs):
        """Ensure only one primary contact per supplier"""
        if self.is_primary:
            # Set all other contacts of this supplier as not primary
            SupplierContact.objects.filter(
                supplier=self.supplier,
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """
    Purchase orders to suppliers
    """
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending Approval')),
        ('APPROVED', _('Approved')),
        ('ORDERED', _('Ordered')),
        ('PARTIALLY_RECEIVED', _('Partially Received')),
        ('RECEIVED', _('Received')),
        ('CANCELLED', _('Cancelled')),
    ]

    po_number = models.CharField(_('PO number'), max_length=20, unique=True, editable=False)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('supplier')
    )
    branch = models.ForeignKey(
        'inventory.Branch',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('branch')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    # People involved
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_purchase_orders',
        verbose_name=_('created by')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders',
        verbose_name=_('approved by')
    )

    # Dates
    order_date = models.DateField(_('order date'), null=True, blank=True)
    expected_delivery_date = models.DateField(_('expected delivery date'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    # Financial information
    subtotal = models.DecimalField(_('subtotal'), max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(_('tax'), max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_('shipping cost'), max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(_('discount'), max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(_('total'), max_digits=12, decimal_places=2, default=0)

    # Additional info
    notes = models.TextField(_('notes'), blank=True)
    supplier_reference = models.CharField(_('supplier reference'), max_length=100, blank=True)

    class Meta:
        verbose_name = _('purchase order')
        verbose_name_plural = _('purchase orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"PO #{self.po_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        # Generate unique PO number if this is a new order
        if not self.po_number:
            self.po_number = self._generate_po_number()

        # Auto-calculate total if not set
        if self.total == 0:
            self.total = self.subtotal + self.tax + self.shipping_cost - self.discount

        super().save(*args, **kwargs)

    def _generate_po_number(self):
        """Generate a unique purchase order number"""
        year = str(timezone.now().year)[2:]  # Last two digits of year
        month = str(timezone.now().month).zfill(2)
        unique = str(uuid.uuid4().int)[:6]
        return f"PO{year}{month}{unique}"


class PurchaseOrderItem(models.Model):
    """
    Items within a purchase order
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('purchase order')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='po_items',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='po_items',
        verbose_name=_('variant')
    )
    quantity_ordered = models.PositiveIntegerField(_('quantity ordered'))
    quantity_received = models.PositiveIntegerField(_('quantity received'), default=0)
    unit_price = models.DecimalField(_('unit price'), max_digits=12, decimal_places=2)
    line_total = models.DecimalField(_('line total'), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _('purchase order item')
        verbose_name_plural = _('purchase order items')

    def __str__(self):
        variant_str = f" - {self.variant}" if self.variant else ""
        return f"{self.product.name}{variant_str} ({self.quantity_ordered}) in PO #{self.purchase_order.po_number}"

    @property
    def is_fully_received(self):
        """Check if all ordered quantity has been received"""
        return self.quantity_received >= self.quantity_ordered

    def save(self, *args, **kwargs):
        # Auto-calculate line total
        self.line_total = self.unit_price * self.quantity_ordered
        super().save(*args, **kwargs)

        # Update parent PO status if needed
        po = self.purchase_order
        all_items = po.items.all()

        # If nothing received yet but status is ordered, keep as is
        if all(item.quantity_received == 0 for item in all_items) and po.status == 'ORDERED':
            pass
        # If all items fully received, mark as received
        elif all(item.is_fully_received for item in all_items):
            po.status = 'RECEIVED'
            po.save(update_fields=['status'])
        # If some items received but not all, mark as partially received
        elif any(item.quantity_received > 0 for item in all_items):
            po.status = 'PARTIALLY_RECEIVED'
            po.save(update_fields=['status'])


class PurchaseOrderReceive(models.Model):
    """
    Receiving records for purchase orders
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='receives',
        verbose_name=_('purchase order')
    )
    receive_date = models.DateField(_('receive date'), default=timezone.now)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='po_receives',
        verbose_name=_('received by')
    )
    reference = models.CharField(_('reference'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('purchase order receive')
        verbose_name_plural = _('purchase order receives')
        ordering = ['-receive_date']

    def __str__(self):
        return f"Receipt for PO #{self.purchase_order.po_number} on {self.receive_date}"


class PurchaseOrderReceiveItem(models.Model):
    """
    Individual items received against a purchase order
    """
    receive = models.ForeignKey(
        PurchaseOrderReceive,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('receive record')
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name='receipt_items',
        verbose_name=_('purchase order item')
    )
    quantity = models.PositiveIntegerField(_('quantity received'))
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('receive item')
        verbose_name_plural = _('receive items')

    def __str__(self):
        return f"{self.quantity} of {self.po_item.product.name} received"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update the received quantity on the PO item
        po_item = self.po_item
        total_received = po_item.receipt_items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

        po_item.quantity_received = total_received
        po_item.save(update_fields=['quantity_received'])

        # This will trigger the PO status update in the PurchaseOrderItem save method