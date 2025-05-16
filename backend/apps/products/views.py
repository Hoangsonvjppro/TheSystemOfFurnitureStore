from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, F, Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import (
    Category, Product, ProductImage, ProductAttribute,
    ProductAttributeValue, ProductVariant, VariantAttributeValue,
    ProductReview, Wishlist, WishlistItem, RecentlyViewed
)
from .serializers import (
    CategorySerializer, CategoryListSerializer, ProductSerializer,
    ProductListSerializer, ProductImageSerializer, ProductAttributeSerializer,
    ProductAttributeValueSerializer, ProductVariantSerializer,
    VariantAttributeValueSerializer, ProductReviewSerializer,
    WishlistSerializer, WishlistItemSerializer, RecentlyViewedSerializer
)
from apps.users.permissions import (
    IsAdminUser, IsAdminOrManager, IsOwner, ReadOnly,
    IsAdminOrManagerOrSalesStaff
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        Return all products in this category and its subcategories
        """
        category = self.get_object()

        # Get all descendant categories including self
        categories = category.get_descendants(include_self=True)

        # Get all products in these categories
        products = Product.objects.filter(
            category__in=categories,
            is_active=True
        ).distinct()

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for products
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_featured', 'supplier']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'price', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManagerOrSalesStaff]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter out inactive products for non-staff users
        """
        queryset = Product.objects.all()

        # Staff users can see all products
        user = self.request.user
        if not (user.is_admin() or user.is_manager() or user.is_sales_staff()):
            queryset = queryset.filter(is_active=True)

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
                # Get all descendant categories including self
                categories = category.get_descendants(include_self=True)
                queryset = queryset.filter(category__in=categories)
            except (Category.DoesNotExist, ValueError):
                pass

        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        return queryset

    @action(detail=True, methods=['post'])
    def add_to_wishlist(self, request, pk=None):
        """
        Add product to user's wishlist
        """
        product = self.get_object()
        user = request.user

        # Get or create wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=user)

        # Check if product already in wishlist
        if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
            return Response(
                {'detail': _('Product already in wishlist')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add to wishlist
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=product
        )

        serializer = WishlistItemSerializer(wishlist_item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_from_wishlist(self, request, pk=None):
        """
        Remove product from user's wishlist
        """
        product = self.get_object()
        user = request.user

        # Get wishlist
        try:
            wishlist = Wishlist.objects.get(user=user)
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product=product)
            wishlist_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (Wishlist.DoesNotExist, WishlistItem.DoesNotExist):
            return Response(
                {'detail': _('Product not in wishlist')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def add_to_recently_viewed(self, request, pk=None):
        """
        Add product to user's recently viewed list
        """
        product = self.get_object()
        user = request.user

        # Update or create recently viewed
        recently_viewed, created = RecentlyViewed.objects.update_or_create(
            user=user,
            product=product,
            defaults={'viewed_at': timezone.now()}
        )

        # Limit recently viewed to 20 items per user
        if not created:
            user_viewed = RecentlyViewed.objects.filter(user=user)
            if user_viewed.count() > 20:
                oldest = user_viewed.order_by('viewed_at').first()
                if oldest:
                    oldest.delete()

        serializer = RecentlyViewedSerializer(recently_viewed)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """
        Add a review to the product
        """
        product = self.get_object()
        user = request.user

        # Check if user already reviewed this product
        if ProductReview.objects.filter(product=product, user=user).exists():
            return Response(
                {'detail': _('You have already reviewed this product')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get data from request
        rating = request.data.get('rating')
        comment = request.data.get('comment')

        # Validate input
        if not rating or not comment:
            return Response(
                {'detail': _('Both rating and comment are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            return Response(
                {'detail': _('Rating must be a number between 1 and 5')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create review
        review = ProductReview.objects.create(
            product=product,
            user=user,
            rating=rating,
            comment=comment,
            is_approved=False  # Require approval by default
        )

        serializer = ProductReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get approved reviews for the product
        """
        product = self.get_object()

        # Staff can see all reviews, others only approved
        if request.user.is_admin() or request.user.is_manager():
            reviews = product.reviews.all()
        else:
            reviews = product.reviews.filter(is_approved=True)

        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """
        Get variants for the product
        """
        product = self.get_object()
        variants = product.variants.filter(is_active=True)

        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """
        Get related products (same category)
        """
        product = self.get_object()

        # Get products in same category, exclude current product
        related = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(pk=product.pk)[:4]

        serializer = ProductListSerializer(related, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products
        """
        featured = Product.objects.filter(is_featured=True, is_active=True)

        page = self.paginate_queryset(featured)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(featured, many=True)
        return Response(serializer.data)


class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product variants
    """
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['sku']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManagerOrSalesStaff]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter out inactive variants for non-staff users
        """
        queryset = ProductVariant.objects.all()

        # Staff users can see all variants
        user = self.request.user
        if not (user.is_admin() or user.is_manager() or user.is_sales_staff()):
            queryset = queryset.filter(is_active=True)

        return queryset


class ProductAttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product attributes
    """
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [permissions.IsAuthenticated & (IsAdminOrManager | ReadOnly)]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'display_name']


class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product reviews
    """
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrManager | IsOwner]
        elif self.action == 'approve':
            permission_classes = [IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter reviews:
        - Admin/Manager: all reviews
        - Others: only approved reviews + their own reviews
        """
        queryset = ProductReview.objects.all()

        # Staff users can see all reviews
        user = self.request.user
        if not (user.is_admin() or user.is_manager()):
            queryset = queryset.filter(Q(is_approved=True) | Q(user=user))

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a review (admin/manager only)
        """
        review = self.get_object()
        review.is_approved = True
        review.save()

        serializer = self.get_serializer(review)
        return Response(serializer.data)


class WishlistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user wishlist (read-only)
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return the user's wishlist"""
        return Wishlist.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """Return the user's wishlist or create one if it doesn't exist"""
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            serializer = self.get_serializer(wishlist)
            return Response(serializer.data)
        except Wishlist.DoesNotExist:
            # Create wishlist
            wishlist = Wishlist.objects.create(user=request.user)
            serializer = self.get_serializer(wishlist)
            return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add item to wishlist
        """
        product_id = request.data.get('product')

        if not product_id:
            return Response(
                {'error': _('Product ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': _('Product not found or inactive')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        # Check if item already in wishlist
        if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
            return Response(
                {'error': _('Product already in wishlist')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add to wishlist
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=product
        )

        # Return updated wishlist
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """
        Remove item from wishlist
        """
        item_id = request.data.get('item_id')

        if not item_id:
            return Response(
                {'error': _('Item ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get wishlist item
        try:
            wishlist_item = WishlistItem.objects.get(
                id=item_id,
                wishlist__user=request.user
            )
        except WishlistItem.DoesNotExist:
            return Response(
                {'error': _('Item not found in wishlist')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete item
        wishlist_item.delete()

        # Return updated wishlist
        wishlist = Wishlist.objects.get(user=request.user)
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear the wishlist
        """
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist.items.all().delete()
            serializer = self.get_serializer(wishlist)
            return Response(serializer.data)
        except Wishlist.DoesNotExist:
            return Response(
                {'error': _('Wishlist not found')},
                status=status.HTTP_404_NOT_FOUND
            )


class RecentlyViewedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for recently viewed products (read-only)
    """
    serializer_class = RecentlyViewedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the user's recently viewed products"""
        return RecentlyViewed.objects.filter(user=self.request.user).order_by('-viewed_at')

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear the recently viewed list
        """
        RecentlyViewed.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)