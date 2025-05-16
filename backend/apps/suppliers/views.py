from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import (
    Supplier, SupplierContact, PurchaseOrder,
    PurchaseOrderItem, PurchaseOrderReceive, PurchaseOrderReceiveItem
)
from .serializers import (
    SupplierSerializer, SupplierContactSerializer,
    PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    PurchaseOrderReceiveSerializer, PurchaseOrderReceiveItemSerializer
)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint for suppliers management
    """
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'city', 'assigned_to']
    search_fields = ['name', 'code', 'email', 'phone', 'description']
    ordering_fields = ['name', 'code', 'created_at']

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get all contacts for a specific supplier"""
        supplier = self.get_object()
        contacts = supplier.contacts.all()
        serializer = SupplierContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def purchase_orders(self, request, pk=None):
        """Get all purchase orders for a specific supplier"""
        supplier = self.get_object()
        purchase_orders = supplier.purchase_orders.all()
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)


class SupplierContactViewSet(viewsets.ModelViewSet):
    """
    API endpoint for supplier contacts management
    """
    queryset = SupplierContact.objects.all()
    serializer_class = SupplierContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['supplier', 'is_primary']
    search_fields = ['name', 'email', 'phone']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for purchase orders management
    """
    queryset = PurchaseOrder.objects.all().order_by('-created_at')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'supplier', 'branch']
    search_fields = ['po_number', 'supplier_reference', 'notes']
    ordering_fields = ['created_at', 'order_date', 'expected_delivery_date', 'total']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase order"""
        purchase_order = self.get_object()
        if purchase_order.status == 'PENDING':
            purchase_order.status = 'APPROVED'
            purchase_order.approved_by = request.user
            purchase_order.save()
            return Response({'status': 'Purchase order approved'})
        return Response(
            {'error': 'Cannot approve order that is not in PENDING status'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a purchase order"""
        purchase_order = self.get_object()
        if purchase_order.status not in ['RECEIVED', 'CANCELLED']:
            purchase_order.status = 'CANCELLED'
            purchase_order.save()
            return Response({'status': 'Purchase order cancelled'})
        return Response(
            {'error': 'Cannot cancel order that is already received or cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items for a specific purchase order"""
        purchase_order = self.get_object()
        items = purchase_order.items.all()
        serializer = PurchaseOrderItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def receives(self, request, pk=None):
        """Get all receive records for a specific purchase order"""
        purchase_order = self.get_object()
        receives = purchase_order.receives.all()
        serializer = PurchaseOrderReceiveSerializer(receives, many=True)
        return Response(serializer.data)


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for purchase order items management
    """
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['purchase_order', 'product']


class PurchaseOrderReceiveViewSet(viewsets.ModelViewSet):
    """
    API endpoint for purchase order receive records management
    """
    queryset = PurchaseOrderReceive.objects.all().order_by('-receive_date')
    serializer_class = PurchaseOrderReceiveSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['purchase_order', 'received_by']
    search_fields = ['reference', 'notes']

    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all receive items for a specific receive record"""
        receive = self.get_object()
        items = receive.items.all()
        serializer = PurchaseOrderReceiveItemSerializer(items, many=True)
        return Response(serializer.data)


class PurchaseOrderReceiveItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for purchase order receive items management
    """
    queryset = PurchaseOrderReceiveItem.objects.all()
    serializer_class = PurchaseOrderReceiveItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['receive', 'po_item']