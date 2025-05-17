from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Sum, Count
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Branch, Stock, StockMovement
from .serializers import (
    BranchSerializer, BranchListSerializer, StockSerializer,
    StockUpdateSerializer, StockMovementSerializer
)
from apps.users.permissions import IsAdminUser, IsInventoryStaff, IsManagerUser, IsAdminOrManagerOrInventoryStaff, \
    IsBranchManager, IsBranchStaff


class BranchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing store branches
    """
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated & (IsAdminUser | IsManagerUser)]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'city']
    search_fields = ['name', 'address', 'city', 'phone', 'email']
    ordering_fields = ['name', 'city', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BranchListSerializer
        return BranchSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['retrieve', 'list']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAdminUser | IsBranchManager]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter branches based on user role:
        - Admin: all branches
        - Manager: only their branch
        - Staff: only their assigned branch
        """
        user = self.request.user
        if user.is_admin():
            return Branch.objects.all()
        elif user.is_manager():
            return Branch.objects.filter(manager=user)
        elif user.branch:
            return Branch.objects.filter(id=user.branch.id)
        return Branch.objects.none()

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Return statistics for the branch"""
        branch = self.get_object()

        # Count total products, low stock, and out of stock
        stock_stats = Stock.objects.filter(branch=branch).aggregate(
            total_products=Count('id'),
            low_stock=Count('id', filter=F('quantity') <= F('reorder_level')),
            out_of_stock=Count('id', filter=F('quantity') <= 0)
        )

        # Count staff by role (excluding admin users)
        staff_by_role = branch.users.exclude(role='ADMIN').values('role').annotate(
            count=Count('id')
        )

        # Movements in last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_movements = StockMovement.objects.filter(
            stock__branch=branch,
            created_at__gte=thirty_days_ago
        ).values('movement_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        )

        return Response({
            'stock': stock_stats,
            'staff': staff_by_role,
            'recent_movements': recent_movements
        })

    @action(detail=True, methods=['get'])
    def low_stock(self, request, pk=None):
        """List low stock items for this branch"""
        branch = self.get_object()

        low_stock = Stock.objects.filter(
            branch=branch,
            quantity__lte=F('reorder_level')
        )

        page = self.paginate_queryset(low_stock)
        if page is not None:
            serializer = StockSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StockSerializer(low_stock, many=True)
        return Response(serializer.data)


class StockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product stock
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated & IsAdminOrManagerOrInventoryStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'product', 'variant']
    search_fields = ['product__name', 'product__sku', 'variant__sku']
    ordering_fields = ['quantity', 'last_restocked']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return StockUpdateSerializer
        return StockSerializer

    def get_queryset(self):
        """
        Filter stocks based on user role:
        - Admin: all stocks
        - Manager: stocks in their branch
        - Staff: stocks in their assigned branch
        """
        user = self.request.user
        if user.is_admin():
            return Stock.objects.all()
        elif user.is_manager() and hasattr(user, 'managed_branch'):
            return Stock.objects.filter(branch=user.managed_branch)
        elif user.branch:
            return Stock.objects.filter(branch=user.branch)
        return Stock.objects.none()

    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """
        Adjust stock quantity with a movement record
        """
        stock = self.get_object()

        # Get the new quantity
        new_quantity = request.data.get('quantity')
        if new_quantity is None:
            return Response(
                {'error': _('Quantity is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_quantity = int(new_quantity)
        except ValueError:
            return Response(
                {'error': _('Quantity must be a number')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate adjustment amount
        adjustment = new_quantity - stock.quantity

        # Create movement record
        if adjustment != 0:
            movement_data = {
                'stock': stock.id,
                'quantity': abs(adjustment),
                'movement_type': 'ADDITION' if adjustment > 0 else 'REMOVAL',
                'reference': request.data.get('reference', ''),
                'notes': request.data.get('notes', _('Stock adjustment')),
                'performed_by': request.user.id
            }

            serializer = StockMovementSerializer(data=movement_data)
            if serializer.is_valid():
                serializer.save()

                # Update stock directly to handle the case of adjustment to exact zero
                stock.quantity = new_quantity
                stock.save(update_fields=['quantity'])

                return Response(StockSerializer(stock).data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # No changes needed
        return Response(StockSerializer(stock).data)

    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """
        Transfer stock to another branch
        """
        stock = self.get_object()
        target_branch_id = request.data.get('target_branch')
        quantity = request.data.get('quantity')

        if not target_branch_id:
            return Response(
                {'error': _('Target branch is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not quantity:
            return Response(
                {'error': _('Quantity is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {'error': _('Quantity must be a positive number')},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > stock.quantity:
            return Response(
                {'error': _('Not enough stock to transfer')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get target branch
        try:
            target_branch = Branch.objects.get(pk=target_branch_id)
        except Branch.DoesNotExist:
            return Response(
                {'error': _('Target branch not found')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create transfer movement
        movement_data = {
            'stock': stock.id,
            'quantity': quantity,
            'movement_type': 'TRANSFER',
            'reference': request.data.get('reference', ''),
            'notes': request.data.get('notes', _('Stock transfer')),
            'performed_by': request.user.id,
            'target_branch': target_branch.id
        }

        serializer = StockMovementSerializer(data=movement_data)
        if serializer.is_valid():
            serializer.save()

            # Get or create stock record at target branch
            target_stock, created = Stock.objects.get_or_create(
                branch=target_branch,
                product=stock.product,
                variant=stock.variant,
                defaults={'quantity': 0, 'reorder_level': stock.reorder_level}
            )

            # Add quantity to target
            target_stock.quantity += quantity
            target_stock.last_restocked = timezone.now()
            target_stock.save()

            return Response({
                'source_stock': StockSerializer(stock).data,
                'target_stock': StockSerializer(target_stock).data,
                'movement': serializer.data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def inventory_report(self, request):
        """
        Generate inventory report with:
        - Total products
        - Low stock items
        - Out of stock items
        - Recent movements
        """
        # Get user's accessible branches
        user = request.user
        if user.is_admin():
            branches = Branch.objects.all()
        elif user.is_manager() and hasattr(user, 'managed_branch'):
            branches = [user.managed_branch]
        elif user.branch:
            branches = [user.branch]
        else:
            branches = []

        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Base queryset
        stocks = Stock.objects.filter(branch__in=branches)

        # Calculate statistics
        stats = stocks.aggregate(
            total_products=Count('id'),
            total_quantity=Sum('quantity'),
            low_stock=Count('id', filter=F('quantity') <= F('reorder_level')),
            out_of_stock=Count('id', filter=F('quantity') <= 0)
        )

        # Get low stock items
        low_stock_items = stocks.filter(quantity__lte=F('reorder_level'))
        low_stock_serializer = StockSerializer(low_stock_items, many=True)

        # Get out of stock items
        out_of_stock_items = stocks.filter(quantity=0)
        out_of_stock_serializer = StockSerializer(out_of_stock_items, many=True)

        # Get recent movements
        movements = StockMovement.objects.filter(stock__branch__in=branches)
        if start_date:
            movements = movements.filter(created_at__gte=start_date)
        if end_date:
            movements = movements.filter(created_at__lte=end_date)

        movement_stats = movements.values('movement_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        )

        return Response({
            'statistics': stats,
            'low_stock_items': low_stock_serializer.data,
            'out_of_stock_items': out_of_stock_serializer.data,
            'movement_statistics': movement_stats
        })


class StockMovementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tracking stock movements
    """
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated & IsAdminOrManagerOrInventoryStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['movement_type', 'stock__branch', 'stock__product', 'performed_by']
    search_fields = ['reference', 'notes', 'stock__product__name']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter movements based on user role:
        - Admin: all movements
        - Manager: movements in their branch
        - Staff: movements in their assigned branch
        """
        user = self.request.user
        if user.is_admin():
            return StockMovement.objects.all()
        elif user.is_manager() and hasattr(user, 'managed_branch'):
            return StockMovement.objects.filter(stock__branch=user.managed_branch)
        elif user.branch:
            return StockMovement.objects.filter(stock__branch=user.branch)
        return StockMovement.objects.none()

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)
