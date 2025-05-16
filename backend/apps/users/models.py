from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom user manager for the User model.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with additional fields and roles for the furniture store system
    """
    # Roles for role-based access control
    ROLE_CHOICES = [
        ('ADMIN', _('Administrator')),
        ('CUSTOMER', _('Customer')),
        ('INVENTORY_STAFF', _('Inventory Staff')),
        ('SALES_STAFF', _('Sales Staff')),
        ('MANAGER', _('Branch Manager')),
    ]

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(_('full name'), max_length=255)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='CUSTOMER',
    )
    branch = models.ForeignKey(
        'inventory.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('assigned branch'),
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name=_('avatar')
    )
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    last_login = models.DateTimeField(_('last login'), auto_now=True)
    is_active = models.BooleanField(_('active'), default=True)

    # Additional permissions
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.'),
    )
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_(
            'Designates that this user has all permissions without '
            'explicitly assigning them.'
        ),
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.username

    # Role-based permission methods
    def is_admin(self):
        return self.role == 'ADMIN' or self.is_superuser

    def is_customer(self):
        return self.role == 'CUSTOMER'

    def is_inventory_staff(self):
        return self.role == 'INVENTORY_STAFF'

    def is_sales_staff(self):
        return self.role == 'SALES_STAFF'

    def is_manager(self):
        return self.role == 'MANAGER'


class UserShippingAddress(models.Model):
    """
    Shipping addresses for users.
    A user can have multiple shipping addresses.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shipping_addresses',
        verbose_name=_('user')
    )
    recipient_name = models.CharField(_('recipient name'), max_length=100)
    phone = models.CharField(_('phone number'), max_length=20)
    address = models.TextField(_('address'))
    city = models.CharField(_('city'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    is_default = models.BooleanField(_('default address'), default=False)

    class Meta:
        verbose_name = _('user shipping address')
        verbose_name_plural = _('user shipping addresses')
        ordering = ['-is_default', 'id']

    def __str__(self):
        return f"{self.recipient_name}, {self.city} ({self.user.email})"

    def save(self, *args, **kwargs):
        # If this address is set as default, unset any other default address for this user
        if self.is_default:
            UserShippingAddress.objects.filter(
                user=self.user,
                is_default=True
            ).update(is_default=False)

        # If this is the first address for the user, make it default
        if not self.pk and not UserShippingAddress.objects.filter(user=self.user).exists():
            self.is_default = True

        super().save(*args, **kwargs)
