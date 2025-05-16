from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

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
    Serializer for user details
    """
    shipping_addresses = UserShippingAddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'phone',
            'address', 'role', 'branch', 'avatar',
            'date_joined', 'is_active', 'shipping_addresses'
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'is_active']
        extra_kwargs = {
            'branch': {'required': False}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users
    """
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'full_name', 'phone', 'address'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'full_name': {'required': True}
        }

    def validate(self, data):
        # Validate that passwords match
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _("Password fields didn't match.")
            })

        # Validate password complexity
        validate_password(data['password'])

        return data

    def create(self, validated_data):
        # Remove password_confirm field
        validated_data.pop('password_confirm')

        # Set role to CUSTOMER by default for user registration
        validated_data['role'] = 'CUSTOMER'

        # Create the user
        user = User.objects.create_user(**validated_data)
        return user


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
