from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import SiteSettings, HomepageBanner, FAQ, ContactMessage, Promotion
from .serializers import (
    SiteSettingsSerializer, HomepageBannerSerializer, FAQSerializer,
    ContactMessageSerializer, ContactMessageAdminSerializer, PromotionSerializer
)
from apps.users.permissions import IsAdminUser, IsAdminOrManager


class SiteSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for site settings
    """
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only admins can modify settings, everyone can view them"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """Return the first site settings object or create one if it doesn't exist"""
        settings = SiteSettings.objects.first()
        if not settings:
            settings = SiteSettings.objects.create(site_name="Furniture Store")
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Redirect to list since we only have one settings object"""
        return self.list(request, *args, **kwargs)


class HomepageBannerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for homepage banners
    """
    queryset = HomepageBanner.objects.all()
    serializer_class = HomepageBannerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['display_order']
    ordering = ['display_order', 'id']

    def get_permissions(self):
        """Only admins can modify banners, everyone can view them"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Only show active banners to non-staff users"""
        queryset = HomepageBanner.objects.all()
        user = self.request.user

        if not (user.is_admin() or user.is_manager()):
            queryset = queryset.filter(is_active=True)

        return queryset

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Return only active banners"""
        active_banners = HomepageBanner.objects.filter(is_active=True).order_by('display_order', 'id')
        serializer = self.get_serializer(active_banners, many=True)
        return Response(serializer.data)


class FAQViewSet(viewsets.ModelViewSet):
    """
    API endpoint for FAQs
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'category']
    search_fields = ['question', 'answer', 'category']
    ordering_fields = ['display_order', 'category']
    ordering = ['display_order', 'id']

    def get_permissions(self):
        """Only admins can modify FAQs, everyone can view them"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Only show active FAQs to non-staff users"""
        queryset = FAQ.objects.all()
        user = self.request.user

        if not (user.is_admin() or user.is_manager()):
            queryset = queryset.filter(is_active=True)

        return queryset

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Return distinct FAQ categories"""
        categories = FAQ.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        return Response(list(filter(None, categories)))  # Filter out empty category values


class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for contact messages
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        - Create: Allow authenticated users
        - List/Retrieve/Update/Delete: Admin only
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOrManager]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Use different serializers for admin vs. user actions"""
        if self.request.user.is_admin() or self.request.user.is_manager():
            return ContactMessageAdminSerializer
        return ContactMessageSerializer

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change message status (admin only)"""
        message = self.get_object()
        status = request.data.get('status')

        if not status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if status not in [s[0] for s in ContactMessage.STATUS_CHOICES]:
            return Response(
                {'error': 'Invalid status value'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message.status = status
        message.save()

        serializer = self.get_serializer(message)
        return Response(serializer.data)


class PromotionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for promotions
    """
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'promo_type']
    search_fields = ['title', 'content']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']

    def get_permissions(self):
        """Only admins can modify promotions, everyone can view them"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Only show active promotions to non-staff users"""
        queryset = Promotion.objects.all()
        user = self.request.user

        if not (user.is_admin() or user.is_manager()):
            queryset = queryset.filter(is_active=True)

        return queryset

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Return only active promotions by type"""
        promo_type = request.query_params.get('type')

        queryset = Promotion.objects.filter(is_active=True)
        if promo_type:
            queryset = queryset.filter(promo_type=promo_type)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)