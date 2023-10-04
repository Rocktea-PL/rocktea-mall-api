from mall.models import CustomUser, Store
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re

class StoreUserSignUp(serializers.ModelSerializer):
   class Meta:
      model=CustomUser
      fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_consumer", "password")
      read_only_fields = ("username", "is_consumer")
      
   def create(self, validated_data):
      # Extract password from validated_data
      password = validated_data.pop("password", None)
      if password:
         # Validate the password using regular expressions
         if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', password):
            raise serializers.ValidationError({"error":"Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter."})

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
   
   def validate(self, attrs):
      # Get Store
      store_id = self.context['request'].query_params.get('store_id')
      
      try:
         store = Store.objects.get(id=store_id)
      except Store.DoesNotExist:
         raise serializers.ValidationError({'error': 'Store not found'})
      
      # Verify User
      data = super().validate(attrs)
      
      # Check if the user is a consumer
      if not self.user.is_consumer:
         raise serializers.ValidationError({'error': 'User is not a consumer'})

      # Add user data to the response
      data['user_data'] = {
         "store": store.name,
         "id": self.user.id,
         "first_name": self.user.first_name,
         "last_name": self.user.last_name,
         "email": self.user.email,
         "username": self.user.username,
         "contact": f"{self.user.contact}",
         "is_volunteer": self.user.is_store_owner
      }

      # Continue with token generation
      refresh = self.get_token(self.user)
      data["refresh"] = str(refresh)
      data["access"] = str(refresh.access_token)
      return data