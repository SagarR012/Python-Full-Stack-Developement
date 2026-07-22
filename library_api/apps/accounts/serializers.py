"""
Accounts Serializers
====================

Serializers convert complex Python objects (Django model instances) to/from
simple Python datatypes that can be rendered into JSON (or other formats).

Teaching Notes:
- Think of serializers as Django Forms for APIs — they handle validation too
- ModelSerializer auto-generates fields from the model (like ModelForm)
- Serializer (base class) is used for non-model data or custom logic
- The validate_<fieldname> pattern is for single-field validation
- The validate() method is for cross-field validation (e.g., password confirmation)
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

# Always use get_user_model() instead of importing User directly.
# This respects the AUTH_USER_MODEL setting and avoids circular imports.
User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles new user registration.

    Why a separate registration serializer?
    - Registration needs a password confirmation field not in the model
    - The password must be write-only (never returned in responses)
    - We need to call user.set_password() to hash the password properly
    """

    # write_only=True means this field is accepted in input but never included
    # in serialized output — critical for passwords!
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],  # Runs Django's built-in password validators
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'bio', 'date_of_birth', 'role'
        ]
        # Make id read-only — it's assigned by the database
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """
        Cross-field validation — runs after individual field validation.
        This is where we confirm the two passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def validate_email(self, value):
        """
        Single-field validation for email uniqueness.
        The validate_<fieldname> pattern is called automatically by DRF.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        """
        Override create() to:
        1. Remove password_confirm (not a model field)
        2. Use create_user() which properly hashes the password
        
        NEVER store passwords as plain text — create_user() calls set_password()
        which runs the password through Django's hasher (PBKDF2 by default).
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)  # Hashes the password securely
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Validates login credentials.

    Note: We use the base Serializer (not ModelSerializer) because this
    doesn't directly represent a model — it's just a validation container.
    The actual token generation is handled by SimpleJWT's TokenObtainPairView.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Used for viewing and updating a user's own profile.

    Security considerations:
    - password is excluded entirely (use ChangePasswordSerializer for that)
    - role is read_only so users can't promote themselves to admin
    - is_staff, is_superuser are excluded to prevent privilege escalation
    """

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'avatar', 'date_of_birth', 'role', 'date_joined'
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Handles password changes for authenticated users.

    Why not use ModelSerializer here?
    - Password changing involves specific logic (verify old, set new)
    - It's not a simple model update
    - This keeps the logic explicit and clear
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        """Confirm the two new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs

    def validate_old_password(self, value):
        """
        Verify the old password is correct.
        We access the current user via self.context['request'].
        The view must pass request in the serializer context.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def save(self, **kwargs):
        """
        Apply the password change.
        Called after validate() passes — the view calls serializer.save().
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for listing users (admin use).
    Includes fewer fields than the full profile for efficiency.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role',
            'is_active', 'date_joined'
        ]

    def get_full_name(self, obj):
        """
        SerializerMethodField calls get_<field_name>().
        Use it for computed/derived fields that aren't model fields.
        """
        return f'{obj.first_name} {obj.last_name}'.strip() or obj.username
