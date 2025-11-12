"""
Serializers for the user API View.
"""
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 5}
        }

    def create(self, validated_data):
        """Create and return user from validated data"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return user from validated data"""
        password = validated_data.pop('password', None)
        user = super().update(instance=instance, validated_data=validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user auth token"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, data):
        """Validate user authentication credentials"""
        email = data.get('email')
        password = data.get('password')
        if not password:
            error_message = _("Bad credentials informations.")
            raise serializers.ValidationError(
                error_message, code='authorization'
            )
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            error_message = _("Email or password is not correct.")
            raise serializers.ValidationError(
                error_message, code='authorization'
            )
        data['user'] = user
        return data
