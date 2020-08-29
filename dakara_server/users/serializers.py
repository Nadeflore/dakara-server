from rest_framework import serializers
from django.contrib.auth import get_user_model, update_session_auth_hash
from dj_rest_auth.serializers import LoginSerializer

UserModel = get_user_model()


class DakaraLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        super().validate(attrs)

        # check if the user is enabled
        user = attrs["user"]
        if user.username == 'flore2':
            raise serializers.ValidationError("This account has not been enabled")

        return attrs


class UserForPublicSerializer(serializers.ModelSerializer):
    """Display public data only
    """

    class Meta:
        model = UserModel
        fields = ("id", "username")
        read_only_fields = ("username",)


class UserSerializer(serializers.ModelSerializer):
    """Creation and view
    """

    class Meta:
        model = UserModel
        fields = (
            "id",
            "username",
            "password",
            "is_superuser",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
        )
        read_only_fields = (
            "is_superuser",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, value):
        """Check username unicity in case insensitive way
        """
        if UserModel.objects.is_username_taken(value):
            raise serializers.ValidationError(
                "The username must be case insensitively unique"
            )

        return value

    def create(self, validated_data):
        """Create a user

        We shouldn't use the parent class method, as it will bypass the
        UserManager's secured user creation methods.
        """
        instance = UserModel.objects.create_user(**validated_data)
        instance.playlist_permission_level = UserModel.USER
        instance.save()

        return instance


class PasswordSerializer(serializers.ModelSerializer):
    """Password edition

    Can edit:
        Password.

    For editing other user info, create another serializer.
    """

    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UserModel
        fields = ("password", "old_password")
        extra_kwargs = {"password": {"write_only": True, "required": True}}

    def validate_old_password(self, value):
        """Check old password is correct
        """
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Wrong password")

    def update(self, instance, validated_data):
        """Update the password
        """
        password = None
        if "password" in validated_data:
            password = validated_data.pop("password")

        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()
            # keep current user logged in
            update_session_auth_hash(self.context["request"], instance)

        return instance


class UserForManagerSerializer(PasswordSerializer):
    """Users edition for managers

    Can edit:
        Apps permission levels,
        Password.
    """

    class Meta:
        model = UserModel
        fields = (
            "password",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
        )
