from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate

from .models import User, UserShippingAddress


class UserShippingAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for user shipping addresses
    """

    class Meta:
        model = UserShippingAddress
        fields = [
            'id', 'recipient_name', 'phone', 'address',
            'city', 'postal_code', 'is_default'
        ]
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user model
    """
    shipping_addresses = UserShippingAddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'phone', 'address',
            'role', 'avatar', 'date_joined', 'shipping_addresses',
            'is_active', 'is_staff',
        )
        read_only_fields = ('id', 'date_joined', 'is_active', 'is_staff', 'role')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a user
    """
    password_confirm = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'phone', 'address',
            'password', 'password_confirm'
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'email': {'required': True},
            'full_name': {'required': True}
        }

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({
                'password': _('Passwords do not match.')
            })

        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password"""
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for the user authentication
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')

            if not user.is_active:
                msg = _('Account is disabled.')
                raise serializers.ValidationError(msg, code='authorization')

        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    current_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        min_length=8
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        min_length=8
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _('New passwords do not match.')
            })

        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Current password is incorrect.'))
        return value


class UserPasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user's password
    """
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Your old password was entered incorrectly."))
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _("Password fields didn't match.")
            })

        validate_password(data['new_password'], self.context['request'].user)
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class StaffUserSerializer(serializers.ModelSerializer):
    """
    Serializer for staff users, used by admin and managers
    """

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'phone',
            'address', 'role', 'branch', 'avatar',
            'date_joined', 'is_active'
        ]

    def validate_role(self, value):
        # Only allow staff roles to be created/modified with this serializer
        allowed_roles = ['SALES_STAFF', 'INVENTORY_STAFF', 'MANAGER']
        if value not in allowed_roles:
            raise serializers.ValidationError(
                _("Role must be one of: {}").format(", ".join(allowed_roles))
            )
        return value


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Limited serializer for customer profile (public view)
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar']
        read_only_fields = ['id', 'username', 'full_name', 'avatar']
