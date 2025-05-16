from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import PurchaseOrder, PurchaseOrderItem, PurchaseOrderReceive

User = get_user_model()


@receiver(post_save, sender=PurchaseOrderItem)
def update_purchase_order_totals(sender, instance, created, **kwargs):
    """
    Update the purchase order totals when an item is added, updated, or deleted
    """
    po = instance.purchase_order
    items = po.items.all()

    # Calculate subtotal
    po.subtotal = sum(item.line_total for item in items)

    # Recalculate the total
    po.total = po.subtotal + po.tax + po.shipping_cost - po.discount

    # Save without triggering additional signals
    PurchaseOrder.objects.filter(id=po.id).update(
        subtotal=po.subtotal,
        total=po.total
    )


@receiver(post_save, sender=PurchaseOrderReceive)
def update_purchase_order_status_on_receive(sender, instance, created, **kwargs):
    """
    Update the purchase order status when a new receive record is created
    """
    if created:
        po = instance.purchase_order

        # Check if this is the first receive for this PO
        if po.status == 'ORDERED':
            po.status = 'PARTIALLY_RECEIVED'
            po.save(update_fields=['status'])

        # This will be further updated by the PurchaseOrderReceiveItem signal
        # which updates the PurchaseOrderItem quantities