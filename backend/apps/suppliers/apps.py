from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SuppliersConfig(AppConfig):
    name = 'apps.suppliers'
    verbose_name = _('Suppliers')

    def ready(self):
        # Import signals để đăng ký các signal handlers
        from . import signals