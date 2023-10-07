from .models import CustomUser, Store
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ReadOnlyField, ValidationError
from .models import CustomUser, Store, Category, SubCategories
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from PIL import Image
from rest_framework import status
from rest_framework import serializers
from django.shortcuts import get_object_or_404

class StoreOwnerSerializer(ModelSerializer):
   class Meta:
      model=CustomUser
      fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_store_owner","password")
      read_only_fields = ("username", "is_store_owner")
      
   def create(self, validated_data):
      # Extract password from validated_data
      password = validated_data.pop("password", None)
      if password:
         # Validate the password using regular expressions
         if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', password):
            raise ValidationError({"error":"Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter."})

      user = CustomUser.objects.create(**validated_data)
      # Confirm the user as a store owner
      user.is_store_owner = True

      if password:
         # Set and save the user's password only if a valid password is provided
         user.set_password(password)
         user.save()
      return user



class CreateStoreSerializer(ModelSerializer):
   class Meta:
      model = Store
      fields = ("id", "owner", "name", "email", "TIN_number", "logo", "year_of_establishment", "category")
      read_only_fields = ("owner",)

   def validate_TIN_number(self, value):
      if isinstance(value, str) and len(value) != 9:  # Check if TIN number has exactly 9 characters
         raise serializers.ValidationError("Invalid TIN number. It should be 9 characters long.")
      return value

   def validate_logo(self, value):
      # check the file extension
      if value:
         file_extension = value.name.split('.')[-1].lower()
         if file_extension not in ['png']:
               raise serializers.ValidationError("Invalid Image format. Only PNG is allowed.")
      return value

   # def validate_category(self, value):
   #    if value:
   #    # Use a dictionary to cache fetched categories to optimize performance
   #       category_cache = getattr(self, '_category_cache', {})
   #       category = category_cache.get(value, None)

   #       if category is None:
   #          # Assuming value is the category ID, not the whole Category object
   #          category = get_object_or_404(Category, id=value)
   #          category_cache[value] = category.id  # Save the category ID
   #          setattr(self, '_category_cache', category_cache)

   #       return category.id  # Return the category ID
   #    return None
      
   def validate_owner(self, value):
      try:
         user = CustomUser.objects.get(is_store_owner=True, id=value)
      except CustomUser.DoesNotExist:
         raise serializers.ValidationError("User with ID {} does not exist or is not a store owner.".format(value))
      return value
   
   def update(self, instance, validated_data):
      # Update the fields of the existing instance with the validated data
      instance.name = validated_data.get('name', instance.name)
      instance.email = validated_data.get('email', instance.email)
      instance.TIN_number = validated_data.get('TIN_number', instance.TIN_number)
      instance.logo = validated_data.get('logo', instance.logo)
      instance.year_of_establishment = validated_data.get('year_of_establishment', instance.year_of_establishment)
      instance.category = validated_data.get('category', instance.category)
      
      # save the updated instance
      instance.save()
      return instance
   
class SubCategorySerializer(ModelSerializer):
   class Meta:
      model = SubCategories
      fields = ["id", "name"]


class CategorySerializer(ModelSerializer):
   subcategories = SubCategorySerializer(many=True, read_only=True)
   category_name = ReadOnlyField(source='name')
   
   class Meta:
      model = Category
      fields = "__all__"
   
   def to_representation(self, instance):
      data = super(CategorySerializer, self).to_representation(instance)
      return {
            "category_id": instance.id,
            "category_name": data["category_name"],
            "subcategories": data["subcategories"]
      }
      

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
   @classmethod
   def get_token(cls, user):
      token = super().get_token(user)
      token['email'] = user.email
      return token
   
   def validate(self, attrs):
      data = super().validate(attrs)
      data['user_data'] = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "username":self.user.username,
            "contact": f"{self.user.contact}",
            "is_volunteer": self.user.is_store_owner
            }
      refresh = self.get_token(self.user)
      data["refresh"] = str(refresh)
      data["access"] = str(refresh.access_token)
      return data
   
# TODO Create Sign Up and Registrationn Logic for Users


