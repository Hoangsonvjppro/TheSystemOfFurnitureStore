from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem, OrderTracking
from .serializers import (
    CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer,
    OrderTrackingSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer,
    OrderPaymentUpdateSerializer, AddToCartSerializer
)
from apps.users.permissions import (
    IsAdminUser, IsManagerUser, IsSalesStaff, IsOwner, IsOwnerOrStaff,
    IsAdminOrManagerOrSalesStaff, IsSalesOrManager
)


class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user's shopping cart.
    Users can only access their own cart.
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return the user's cart"""
        return Cart.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """Return the user's cart or create one if it doesn't exist"""
        try:
            cart = Cart.objects.get(user=request.user)
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            # Create cart
            cart = Cart.objects.create(user=request.user)
            serializer = self.get_serializer(cart)
            return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add item to cart.
        If the item already exists, the quantity will be increased.
        """
        # Use a different serializer for adding items
        from apps.products.models import Product, ProductVariant

        product_id = request.data.get('product')
        variant_id = request.data.get('variant')
        quantity = int(request.data.get('quantity', 1))

        # Validate product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': _('Product not found or inactive')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate variant if provided
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id,
                    product=product,
                    is_active=True
                )
            except ProductVariant.DoesNotExist:
                return Response(
                    {'error': _('Variant not found or inactive')},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if item exists
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            # Update quantity
            cart_item.quantity += quantity
            cart_item.save()

        # Return updated cart
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Update item quantity in cart"""
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')

        if not item_id or not quantity:
            return Response(
                {'error': _('Item ID and quantity are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {'error': _('Quantity must be greater than zero')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': _('Quantity must be a number')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get cart item
        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response(
                {'error': _('Item not found in cart')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()

        # Return updated cart
        cart = Cart.objects.get(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        item_id = request.data.get('item_id')

        if not item_id:
            return Response(
                {'error': _('Item ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get cart item
        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response(
                {'error': _('Item not found in cart')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete item
        cart_item.delete()

        # Return updated cart
        cart = Cart.objects.get(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear the cart"""
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response(
                {'error': _('Cart not found')},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for orders
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'branch']
    search_fields = ['order_number', 'shipping_name', 'shipping_phone']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter orders based on user role:
        - Admin & Manager: all orders
        - Sales Staff: orders in their branch
        - Customer: their own orders
        """
        user = self.request.user

        if user.is_admin():
            return Order.objects.all().select_related('user', 'branch')
        elif user.is_manager() and hasattr(user, 'managed_branch'):
            return Order.objects.filter(branch=user.managed_branch).select_related('user', 'branch')
        elif user.is_sales_staff() and user.branch:
            return Order.objects.filter(branch=user.branch).select_related('user', 'branch')
        else:
            # Regular customer
            return Order.objects.filter(user=user).select_related('user', 'branch')

    def get_serializer_class(self):
        """
        Return appropriate serializer class
        """
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        elif self.action == 'update_payment':
            return OrderPaymentUpdateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """
        Create an order from the user's cart
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Return created order
        order_serializer = OrderSerializer(order)
        return Response(
            order_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status
        """
        if not (request.user.is_admin() or request.user.is_manager() or request.user.is_sales_staff()):
            return Response(
                {'success': False, 'message': _('You do not have permission to perform this action')},
                status=status.HTTP_403_FORBIDDEN
            )
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            order,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()
        order_serializer = OrderSerializer(updated_order)
        return Response({'success': True, 'message': _('Order status updated successfully'), 'order': order_serializer.data})

    @action(detail=True, methods=['post'])
    def update_payment(self, request, pk=None):
        """
        Update payment status and method
        """
        if not (request.user.is_admin() or request.user.is_manager() or request.user.is_sales_staff()):
            return Response(
                {'success': False, 'message': _('You do not have permission to perform this action')},
                status=status.HTTP_403_FORBIDDEN
            )
        order = self.get_object()
        serializer = OrderPaymentUpdateSerializer(
            order,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()
        order_serializer = OrderSerializer(updated_order)
        return Response({'success': True, 'message': _('Order payment updated successfully'), 'order': order_serializer.data})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an order
        """
        order = self.get_object()
        if not (request.user.is_admin() or request.user.is_manager() or
                request.user.is_sales_staff() or request.user == order.user):
            return Response(
                {'success': False, 'message': _('You do not have permission to perform this action')},
                status=status.HTTP_403_FORBIDDEN
            )
        if order.status not in ['PENDING', 'CONFIRMED', 'PROCESSING']:
            return Response(
                {'success': False, 'message': _('This order cannot be cancelled')},
                status=status.HTTP_400_BAD_REQUEST
            )
        notes = request.data.get('notes', _('Order cancelled by user'))
        order.status = 'CANCELLED'
        order.cancelled_at = timezone.now()
        order.save()
        OrderTracking.objects.create(
            order=order,
            status='CANCELLED',
            notes=notes,
            performed_by=request.user
        )
        serializer = OrderSerializer(order)
        return Response({'success': True, 'message': _('Order cancelled successfully'), 'order': serializer.data})

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        Return the user's orders
        """
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(orders)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Return order statistics for dashboard (admin/manager only)
        """
        # Only admin and managers can access dashboard
        if not (request.user.is_admin() or request.user.is_manager()):
            return Response(
                {'error': _('You do not have permission to perform this action')},
                status=status.HTTP_403_FORBIDDEN
            )

        # Filter orders based on user role
        if request.user.is_manager() and hasattr(request.user, 'managed_branch'):
            orders = Order.objects.filter(branch=request.user.managed_branch)
        elif request.user.is_admin():
            orders = Order.objects.all()
        else:
            orders = Order.objects.none()

        # Last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_orders = orders.filter(created_at__gte=thirty_days_ago)

        # Calculate statistics
        stats = {
            'total_orders': orders.count(),
            'recent_orders': recent_orders.count(),
            'pending_orders': orders.filter(status='PENDING').count(),
            'confirmed_orders': orders.filter(status='CONFIRMED').count(),
            'processing_orders': orders.filter(status='PROCESSING').count(),
            'shipped_orders': orders.filter(status='SHIPPED').count(),
            'delivered_orders': orders.filter(status='DELIVERED').count(),
            'cancelled_orders': orders.filter(status='CANCELLED').count(),
            'payment_pending': orders.filter(payment_status='PENDING').count(),
            'payment_completed': orders.filter(payment_status='PAID').count(),
        }

        return Response(stats)

    @action(detail=True, methods=['post'], permission_classes=[IsSalesOrManager])
    def approve(self, request, pk=None):
        """
        Approve (duyệt) một đơn hàng. Chỉ Sales hoặc Manager mới được duyệt.
        """
        order = self.get_object()
        if order.status == 'APPROVED':
            return Response({'success': False, 'message': _('Order is already approved.')}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'APPROVED'
        order.approved_by = request.user
        order.approved_at = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response({'success': True, 'message': _('Order approved successfully'), 'order': serializer.data})


class OrderTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for order tracking history (read-only)
    """
    serializer_class = OrderTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter tracking based on user role and order ID
        """
        order_id = self.kwargs.get('order_pk')
        user = self.request.user

        # Check if order exists and user has permission
        try:
            if user.is_admin():
                order = Order.objects.get(id=order_id)
            elif user.is_manager() and hasattr(user, 'managed_branch'):
                order = Order.objects.get(id=order_id, branch=user.managed_branch)
            elif user.is_sales_staff() and user.branch:
                order = Order.objects.get(id=order_id, branch=user.branch)
            else:
                # Regular customer
                order = Order.objects.get(id=order_id, user=user)

            return order.tracking_history.all().order_by('-timestamp')

        except Order.DoesNotExist:
            return OrderTracking.objects.none()
