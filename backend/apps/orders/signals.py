from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, OrderItem, Cart, CartItem
from apps.inventory.models import Stock, StockMovement


@receiver(post_save, sender=Order)
def update_order_status_timestamps(sender, instance, created, **kwargs):
    """
    Update timestamps when order status changes
    """
    # Status timestamps already handled in the save method of Order model
    pass


@receiver(post_save, sender=Order)
def handle_order_confirmation(sender, instance, created, **kwargs):
    """
    When an order is confirmed, reduce inventory
    """
    if not created and instance.status == 'CONFIRMED':
        # Reduce stock for each order item
        for item in instance.items.all():
            if item.variant:
                stock = Stock.objects.filter(
                    branch=instance.branch,
                    product=item.product,
                    variant=item.variant
                ).first()
            else:
                stock = Stock.objects.filter(
                    branch=instance.branch,
                    product=item.product,
                    variant__isnull=True
                ).first()

            if stock:
                # Create stock movement
                StockMovement.objects.create(
                    stock=stock,
                    quantity=item.quantity,
                    movement_type='REMOVAL',
                    reference=f"Order #{instance.order_number}",
                    notes=f"Order confirmed: {item.product_name}",
                    performed_by=instance.processed_by
                )


@receiver(post_save, sender=Order)
def handle_order_cancellation(sender, instance, created, **kwargs):
    """
    When an order is cancelled after confirmation, restore inventory
    """
    if not created and instance.status == 'CANCELLED' and instance.confirmed_at:
        # Restore stock for each order item
        for item in instance.items.all():
            if item.variant:
                stock = Stock.objects.filter(
                    branch=instance.branch,
                    product=item.product,
                    variant=item.variant
                ).first()
            else:
                stock = Stock.objects.filter(
                    branch=instance.branch,
                    product=item.product,
                    variant__isnull=True
                ).first()

            if stock:
                # Create stock movement to restore inventory
                StockMovement.objects.create(
                    stock=stock,
                    quantity=item.quantity,
                    movement_type='ADDITION',
                    reference=f"Order #{instance.order_number}",
                    notes=f"Order cancelled: {item.product_name}",
                    performed_by=instance.processed_by
                )


@receiver(post_save, sender=CartItem)
def update_cart_timestamp(sender, instance, **kwargs):
    """
    Update cart timestamp when a cart item is added or modified
    """
    cart = instance.cart
    cart.updated_at = timezone.now()
    cart.save(update_fields=['updated_at'])


@receiver(pre_delete, sender=CartItem)
def update_cart_timestamp_on_delete(sender, instance, **kwargs):
    """
    Update cart timestamp when a cart item is removed
    """
    cart = instance.cart
    cart.updated_at = timezone.now()
    cart.save(update_fields=['updated_at'])