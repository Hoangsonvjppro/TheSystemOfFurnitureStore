from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import SiteSettings, HomepageBanner, FAQ, ContactMessage, Promotion


class SiteSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for site settings
    """

    class Meta:
        model = SiteSettings
        fields = (
            'id', 'site_name', 'site_logo', 'favicon', 'address',
            'email', 'phone', 'facebook_url', 'instagram_url',
            'twitter_url', 'youtube_url', 'about_us', 'privacy_policy',
            'terms_conditions', 'shipping_policy', 'return_policy',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class HomepageBannerSerializer(serializers.ModelSerializer):
    """
    Serializer for homepage banners
    """

    class Meta:
        model = HomepageBanner
        fields = (
            'id', 'title', 'subtitle', 'image', 'button_text',
            'button_link', 'is_active', 'display_order',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class FAQSerializer(serializers.ModelSerializer):
    """
    Serializer for frequently asked questions
    """

    class Meta:
        model = FAQ
        fields = (
            'id', 'question', 'answer', 'category',
            'is_active', 'display_order', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for contact messages
    """

    class Meta:
        model = ContactMessage
        fields = (
            'id', 'name', 'email', 'phone', 'subject',
            'message', 'status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'status', 'created_at', 'updated_at')

    def validate_email(self, value):
        """Validate email format"""
        if not value:
            raise serializers.ValidationError(_("Email is required"))
        return value

    def validate_message(self, value):
        """Validate message content"""
        if not value or len(value) < 10:
            raise serializers.ValidationError(_("Message must be at least 10 characters"))
        return value


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    """
    Admin serializer for contact messages with status update capability
    """

    class Meta:
        model = ContactMessage
        fields = (
            'id', 'name', 'email', 'phone', 'subject',
            'message', 'status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'name', 'email', 'phone', 'subject', 'message', 'created_at', 'updated_at')


class PromotionSerializer(serializers.ModelSerializer):
    """
    Serializer for promotions
    """

    class Meta:
        model = Promotion
        fields = (
            'id', 'title', 'content', 'promo_type', 'image',
            'url', 'start_date', 'end_date', 'is_active',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        """Validate promotion dates"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': _("End date must be after start date")
            })

        return attrs