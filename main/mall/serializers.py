from .models import CustomUser
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ReadOnlyField, ValidationError
from .models import CustomUser, Store, Category, SubCategories
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from PIL import Image
from rest_framework import status

class StoreOwnerSerializer(ModelSerializer):
   class Meta:
      model=CustomUser
      fields = ("uid", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_store_owner","password")
      
   
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
        fields = ("id", "owner", "name", "email", "TIN_number", "logo", "year_of_establishment", "domain_name", "category", "store_url")
   
   def validate_TIN_number(self, value):
      if isinstance(value, str) and len(value) != 9:  # Check if TIN number has exactly 9 characters
         raise serializers.ValidationError("Invalid TIN number. It should be 9 characters long.")
      return value
   
   def validate_logo(self, value):
      if value:
         try:
               img = Image.open(value)
               img_format = img.format.lower()
               if img_format not in ['png', 'jpeg', 'jpg']:
                  raise ValidationError("Invalid Image format. Only PNG and JPEG are allowed.")
         except Exception as e:
               raise ValidationError("Invalid image file. Please upload a valid image")
      return value
    
   # def create(self, validated_data):
   #    owner_uid = self.context.get('request').user.uid
   #    verified_owner = self._verify_owner(owner_uid)
      
   #    if verified_owner is None:
   #       raise ValidationError({"error": "Sorry, you can only have one store."})
      
   #    validated_data['owner'] = verified_owner
   #    store = Store.objects.create(**validated_data)
   #    return store
      
   # def _verify_owner(self, owner_uid):
   #    owner = CustomUser.objects.filter(is_store_owner=True, owner=owner_uid).first()
   #    return owner
      
    
   
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
            "uid": self.user.uid,
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
    
   #  def validate(self, attrs):
   #      data = super().validate(attrs)
   #      data['user_data'] = {
   #          "uid": self.user.uid,
   #          "first_name": self.user.first_name,
   #          "last_name": self.user.last_name,
   #          "email": self.user.email,
   #          "username":self.user.username,
   #          "contact": f"{self.user.contact}",
   #          "is_volunteer": self.user.is_store_owner
   #          }
   #      refresh = self.get_token(self.user)
   #      data["refresh"] = str(refresh)
   #      data["access"] = str(refresh.access_token)
   #      return data