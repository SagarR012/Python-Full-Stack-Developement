"""
Accounts Serializers — Student Management API
==============================================

COMPARE WITH: library_api/apps/accounts/serializers.py

Same patterns:
- write_only=True on passwords
- validate() for cross-field validation (password confirmation)
- validate_<field> for single-field validation
- HiddenField for auto-set fields
- Multiple serializers per model for different use cases

STUDENT EXERCISE:
1. The UserRegistrationSerializer sets role from the request.
   Add validation: only admins can create users with role='admin'.
   Hint: use self.context['request'].user in validate()
2. Add a validate_phone_number method to check format
3. Create a TeacherListSerializer that includes the courses they teach
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration.

    Key points:
    - password and password_confirm are write_only (never returned)
    - validate() checks they match
    - create() uses set_password() to hash the password securely
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
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
            'phone_number', 'bio', 'role',
            'password', 'password_confirm',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """Cross-field: passwords must match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def validate_email(self, value):
        """Email must be unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        """
        Hash the password and create the user.

        NEVER save a plain-text password. set_password() runs the password
        through Django's password hasher (PBKDF2 by default).
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    For viewing and updating your own profile.

    Security:
    - role is read_only (users can't promote themselves)
    - password excluded (use ChangePasswordSerializer)
    - date_joined is read_only (set by Django)
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'bio', 'role', 'date_joined'
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    """
    Handles password change for authenticated users.

    Uses base Serializer (not ModelSerializer) because this isn't a
    simple model update — it requires verifying the old password first.
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
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs

    def validate_old_password(self, value):
        """
        Verify the current password.
        Access the user via self.context['request'] — the view must pass it.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users (admin view)."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role', 'is_active', 'date_joined']

    def get_full_name(self, obj):
        """SerializerMethodField — calls get_full_name(obj)."""
        return f'{obj.first_name} {obj.last_name}'.strip() or obj.username
