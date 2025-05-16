from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'suppliers'

router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'contacts', views.SupplierContactViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'purchase-order-items', views.PurchaseOrderItemViewSet)
router.register(r'purchase-order-receives', views.PurchaseOrderReceiveViewSet)
router.register(r'purchase-order-receive-items', views.PurchaseOrderReceiveItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]