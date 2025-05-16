from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('', views.UserViewSet, basename='users')
router.register('shipping-addresses', views.UserShippingAddressViewSet, basename='shipping-addresses')

urlpatterns = [
    path('', include(router.urls)),
    path('customers/<int:pk>/', views.CustomerProfileView.as_view(), name='customer-profile'),
]
