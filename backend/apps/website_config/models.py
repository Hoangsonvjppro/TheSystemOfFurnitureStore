from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """
    General site-wide settings
    """
    site_name = models.CharField(_('site name'), max_length=100)
    site_logo = models.ImageField(_('site logo'), upload_to='site/', null=True, blank=True)
    favicon = models.ImageField(_('favicon'), upload_to='site/', null=True, blank=True)
    address = models.TextField(_('address'), blank=True)
    email = models.EmailField(_('contact email'), blank=True)
    phone = models.CharField(_('contact phone'), max_length=20, blank=True)
    facebook_url = models.URLField(_('Facebook URL'), blank=True)
    instagram_url = models.URLField(_('Instagram URL'), blank=True)
    twitter_url = models.URLField(_('Twitter URL'), blank=True)
    youtube_url = models.URLField(_('YouTube URL'), blank=True)
    about_us = models.TextField(_('about us'), blank=True)
    privacy_policy = models.TextField(_('privacy policy'), blank=True)
    terms_conditions = models.TextField(_('terms and conditions'), blank=True)
    shipping_policy = models.TextField(_('shipping policy'), blank=True)
    return_policy = models.TextField(_('return policy'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('site settings')
        verbose_name_plural = _('site settings')

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance of settings exists
        if not self.pk and SiteSettings.objects.exists():
            # Update existing instance instead of creating a new one
            existing = SiteSettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class HomepageBanner(models.Model):
    """
    Homepage banner/slider images
    """
    title = models.CharField(_('title'), max_length=100)
    subtitle = models.CharField(_('subtitle'), max_length=200, blank=True)
    image = models.ImageField(_('image'), upload_to='banners/')
    button_text = models.CharField(_('button text'), max_length=50, blank=True)
    button_link = models.CharField(_('button link'), max_length=200, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('homepage banner')
        verbose_name_plural = _('homepage banners')
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """
    Frequently Asked Questions
    """
    question = models.CharField(_('question'), max_length=255)
    answer = models.TextField(_('answer'))
    category = models.CharField(_('category'), max_length=100, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    """
    Contact form messages from users
    """
    STATUS_CHOICES = [
        ('NEW', _('New')),
        ('READ', _('Read')),
        ('REPLIED', _('Replied')),
        ('CLOSED', _('Closed')),
    ]

    name = models.CharField(_('name'), max_length=100)
    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    subject = models.CharField(_('subject'), max_length=200)
    message = models.TextField(_('message'))
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('contact message')
        verbose_name_plural = _('contact messages')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.subject}"


class Promotion(models.Model):
    """
    Promotional information like banners, popups, etc.
    """
    TYPE_CHOICES = [
        ('BANNER', _('Banner')),
        ('POPUP', _('Popup')),
        ('ANNOUNCEMENT', _('Announcement')),
    ]

    title = models.CharField(_('title'), max_length=100)
    content = models.TextField(_('content'))
    promo_type = models.CharField(_('type'), max_length=20, choices=TYPE_CHOICES)
    image = models.ImageField(_('image'), upload_to='promotions/', null=True, blank=True)
    url = models.CharField(_('URL'), max_length=200, blank=True)
    start_date = models.DateTimeField(_('start date'))
    end_date = models.DateTimeField(_('end date'))
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('promotion')
        verbose_name_plural = _('promotions')
        ordering = ['-start_date']

    def __str__(self):
        return self.title