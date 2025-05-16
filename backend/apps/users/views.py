from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from .models import User, UserShippingAddress
from .serializers import (
    UserSerializer, UserCreateSerializer, UserPasswordChangeSerializer,
    UserShippingAddressSerializer, StaffUserSerializer, CustomerProfileSerializer
)
from .permissions import (
    IsAdmin, IsAdminOrManager, IsOwner, IsOwnerOrStaff
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'change_password':
            return UserPasswordChangeSerializer
        elif self.action == 'staff_list' or self.action == 'create_staff':
            return StaffUserSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy', 'change_password']:
            return [permissions.IsAuthenticated(), IsOwnerOrStaff()]
        elif self.action in ['list', 'staff_list', 'create_staff']:
            return [permissions.IsAuthenticated(), IsAdminOrManager()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # Admins and managers can see all users
        if user.is_admin() or user.is_manager():
            return User.objects.all()
        # Regular users can only see themselves
        return User.objects.filter(id=user.id)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the authenticated user's details
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """
        Change a user's password
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': _('Password changed successfully')}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def staff_list(self, request):
        """
        List all staff users (for admin and managers)
        """
        staff_users = User.objects.filter(
            role__in=['SALES_STAFF', 'INVENTORY_STAFF', 'MANAGER']
        )

        # Managers can only see staff in their branch
        if request.user.is_manager() and request.user.branch:
            staff_users = staff_users.filter(branch=request.user.branch)

        serializer = self.get_serializer(staff_users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_staff(self, request):
        """
        Create a new staff user (for admin and managers)
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set branch to manager's branch if not specified
            if request.user.is_manager() and request.user.branch and not serializer.validated_data.get('branch'):
                serializer.validated_data['branch'] = request.user.branch

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserShippingAddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user shipping addresses
    """
    serializer_class = UserShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return UserShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set an address as the default shipping address
        """
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({'message': _('Address set as default')}, status=status.HTTP_200_OK)


class CustomerProfileView(generics.RetrieveAPIView):
    """
    Public endpoint to view basic customer profile information
    """
    queryset = User.objects.filter(role='CUSTOMER', is_active=True)
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
