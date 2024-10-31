from mall.models import CustomUser, Store
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from django.shortcuts import get_object_or_404
from workshop.processor import DomainNameHandler

handler = DomainNameHandler()

def get_store_domain(request):
   return request.META.get("HTTP_ORIGIN")


class StoreUserSignUpSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_consumer", "associated_domain", "password")
        read_only_fields = ("username", "is_consumer", "associated_domain")

    def validate_password(self, value):
        if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', value):
            raise serializers.ValidationError("Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        store_instance = None
        
        if 'store_domain' in validated_data:
            domain_host = handler.process_request(store_domain=get_store_domain(self.context['request']))
            store_instance = get_object_or_404(Store, id=domain_host)

        user = CustomUser.objects.create(associated_domain=store_instance, **validated_data)

        user.is_consumer = True

        if password:
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password', None)  # Remove the password field from the response
        return representation

class UserLogin(TokenObtainPairSerializer):
   @classmethod
   def get_token(cls, user):
      token = super().get_token(user)
      token['email'] = user.email
      return token

   def get_store(self, user):
      store_id = self.context['request'].query_params.get('store_id')
      
      if store_id:
         try:
               return Store.objects.get(id=store_id)
         except Store.DoesNotExist:
               raise serializers.ValidationError({'error': 'Store not found'})
      elif user.associated_domain:
         return user.associated_domain
      else:
         return None

   def validate(self, attrs):
      data = super().validate(attrs)
      
      if not self.user.is_consumer:
         raise serializers.ValidationError({'error': 'User is not a consumer'})

      store = self.get_store(self.user)
      
      user_data = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "username": self.user.username,
            "contact": str(self.user.contact),
            "is_store_owner": self.user.is_store_owner,
        }

      if store:
         user_data['store_data'] = {
               "store": store.name,
               "id": store.id,
         }

      data['user_data'] = user_data

      refresh = self.get_token(self.user)
      data["refresh"] = str(refresh)
      data["access"] = str(refresh.access_token)

      return data