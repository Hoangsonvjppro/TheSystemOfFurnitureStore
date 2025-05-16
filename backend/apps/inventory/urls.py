from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BranchViewSet, StockViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'stocks', StockViewSet)
router.register(r'stock-movements', StockMovementViewSet)

app_name = 'inventory'

urlpatterns = [
    path('', include(router.urls)),
]
