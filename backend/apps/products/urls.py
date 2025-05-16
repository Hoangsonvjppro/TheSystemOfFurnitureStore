from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, ProductViewSet, ProductVariantViewSet,
    ProductAttributeViewSet, ProductReviewViewSet,
    WishlistViewSet, RecentlyViewedViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'attributes', ProductAttributeViewSet, basename='attribute')
router.register(r'reviews', ProductReviewViewSet, basename='review')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'recently-viewed', RecentlyViewedViewSet, basename='recently-viewed')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
]