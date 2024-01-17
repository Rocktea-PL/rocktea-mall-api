from mall.models import CustomUser, Store
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from django.shortcuts import get_object_or_404


class StoreUserSignUp(serializers.ModelSerializer):
   associated_domain = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all(), required=True)
   class Meta:
      model = CustomUser
      fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "associated_domain", "is_consumer", "password")
      read_only_fields = ("username", "is_consumer")

   def validate_password(self, value):
      if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', value):
         raise serializers.ValidationError("Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter.")
      return value

   def create(self, validated_data):
      # Extract password from validated_data
      password = validated_data.pop("password", None)

      user = CustomUser.objects.create(**validated_data)
      
      # Confirm the user as a store owner
      user.is_consumer = True

      if password:
         # Set and save the user's password only if a valid password is provided
         user.set_password(password)
         user.save()

      return user


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
      
      if store:
         data['user_data'] = {
               "id": self.user.id,
               "first_name": self.user.first_name,
               "last_name": self.user.last_name,
               "email": self.user.email,
               "username": self.user.username,
               "contact": str(self.user.contact),
               "is_store_owner": self.user.is_store_owner,
               'store_data': {
                  "store": store.name,
                  "id": store.id,
                  # "category": store.category.id
               },
         }

         refresh = self.get_token(self.user)
         data["refresh"] = str(refresh)
         data["access"] = str(refresh.access_token)

      return data