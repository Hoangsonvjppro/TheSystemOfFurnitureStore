from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import User


@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    """
    Create related models for a new user (e.g., cart, wishlist)
    """
    if created:
        # Import here to avoid circular imports
        from apps.orders.models import Cart

        # Create a cart for the user
        Cart.objects.create(customer=instance)

        # Create a wishlist for the user (if Wishlist model is implemented)
        try:
            from apps.products.models import Wishlist
            Wishlist.objects.create(user=instance)
        except ImportError:
            # Wishlist model might not be implemented yet
            pass


@receiver(pre_save, sender=User)
def handle_role_change(sender, instance, **kwargs):
    """
    Handle actions when a user's role changes
    """
    # Check if this is an existing user (not a new one)
    if instance.pk:
        try:
            # Get the previous state of the user
            old_instance = User.objects.get(pk=instance.pk)

            # If role has changed, perform role-specific actions
            if old_instance.role != instance.role:
                # For example, if user becomes MANAGER, we might need to do something
                if instance.role == 'MANAGER' and not instance.branch:
                    # Log a warning or take appropriate action
                    pass

                # If user is no longer SALES_STAFF or INVENTORY_STAFF,
                # might need to reassign their tasks
                if old_instance.role in ['SALES_STAFF', 'INVENTORY_STAFF'] and \
                        instance.role not in ['SALES_STAFF', 'INVENTORY_STAFF']:
                    # Reassign tasks/orders or take appropriate action
                    pass

        except User.DoesNotExist:
            # This should not happen, but just in case
            pass