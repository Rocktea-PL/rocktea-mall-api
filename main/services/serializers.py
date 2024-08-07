from rest_framework import serializers
from mall.models import CustomUser, ServicesBusinessInformation
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from .models import ServicesCategory


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "first_name", "last_name", "username", "email", "contact", "type",
                  "profile_image", "is_services", "password")
        read_only_fields = ("username", "is_services")

    def create(self, validated_data):
        # Extract password from validated_data
        password = validated_data.pop("password", None)
        if password:
            # Validate the password using regular expressions
            if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', password):
                raise ValidationError(
                    {"error": "Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter."})

        user = CustomUser.objects.create(**validated_data)
        # Confirm the user as a store owner
        user.is_services = True

        if password:
            # Set and save the user's password only if a valid password is provided
            user.set_password(password)
            user.save()
        return user


class ServicesLogin(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_id = self.user.id

        try:
            user = ServicesBusinessInformation.objects.get(user=user_id)
            has_service = True
        except ServicesBusinessInformation.DoesNotExist:
            has_service = False

        data['user_data'] = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "username": self.user.username,
            "contact": str(self.user.contact),
            "is_services": self.user.is_services,
            "type": self.user.type,
            "has_service": has_service
        }

        refresh = self.get_token(self.user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        return data


class ServicesCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicesCategory
        fields = "__all__"
