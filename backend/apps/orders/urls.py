from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import CartViewSet, OrderViewSet, OrderTrackingViewSet

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')

# Nested router for order tracking
orders_router = NestedSimpleRouter(router, r'orders', lookup='order')
orders_router.register(r'tracking', OrderTrackingViewSet, basename='order-tracking')

app_name = 'orders'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(orders_router.urls)),
]
