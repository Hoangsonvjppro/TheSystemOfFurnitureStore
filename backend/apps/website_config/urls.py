from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SiteSettingsViewSet, HomepageBannerViewSet, FAQViewSet,
    ContactMessageViewSet, PromotionViewSet
)

router = DefaultRouter()
router.register(r'settings', SiteSettingsViewSet, basename='settings')
router.register(r'banners', HomepageBannerViewSet, basename='banner')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'contact', ContactMessageViewSet, basename='contact')
router.register(r'promotions', PromotionViewSet, basename='promotion')

app_name = 'website_config'

urlpatterns = [
    path('', include(router.urls)),
]