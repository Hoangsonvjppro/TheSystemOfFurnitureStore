from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WebsiteConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.website_config'
    verbose_name = _('Website Configuration')

    def ready(self):
        # Import any signals here if needed in the future
        pass