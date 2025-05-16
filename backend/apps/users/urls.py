from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# Đăng ký UserViewSet cho endpoint gốc (quản lý người dùng)
router.register('', views.UserViewSet, basename='users')
# Đăng ký UserShippingAddressViewSet cho endpoint quản lý địa chỉ giao hàng
router.register('shipping-addresses', views.UserShippingAddressViewSet, basename='shipping-addresses')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint xem thông tin profile của khách hàng theo id
    path('customers/<int:pk>/', views.CustomerProfileView.as_view(), name='customer-profile'),
]
