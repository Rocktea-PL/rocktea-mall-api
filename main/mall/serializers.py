from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ReadOnlyField, ValidationError
from .models import CustomUser, Store, Category, SubCategories, Size, Price, Product, Brand, ProductTypes, ProductImage, MarketPlace
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
from PIL import Image
from rest_framework import status
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.core.cache import cache
from setup.celery import app


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


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
   @classmethod
   def get_token(cls, user):
      token = super().get_token(user)
      token['email'] = user.email
      return token
   
   def validate(self, attrs):
      data = super().validate(attrs)
      user_id = self.user.id
      
      try:
         user = CustomUser.objects.get(is_store_owner=True, id=user_id)
      except CustomUser.DoesNotExist:
         raise serializers.ValidationError("User Does Not Exist")
      
      try:
         store = Store.objects.get(owner=user)
         has_store = True
      except Store.DoesNotExist:
         has_store = False
      
      data['user_data'] = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "username":self.user.username,
            "contact": f"{self.user.contact}",
            "is_storeowner": self.user.is_store_owner,
            "has_store": has_store
            }
      
      refresh = self.get_token(self.user)
      data["refresh"] = str(refresh)
      data["access"] = str(refresh.access_token)
      return data


class CreateStoreSerializer(ModelSerializer):
   class Meta:
      model = Store
      fields = ("id", "owner", "name", "email", "TIN_number", "logo", "year_of_establishment", "category", "associated_domain")
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
      
   def validate_owner(self, value):
      if value is None:
         return value  # If owner is None, no validation is needed

      try:
         user = CustomUser.objects.get(is_store_owner=True, id=value)
      except CustomUser.DoesNotExist:
         raise serializers.ValidationError("User with ID {} does not exist or is not a store owner.".format(value))
      return value
   
   def update(self, instance, validated_data):
         for field in ["name", "email", "TIN_number", "logo", "year_of_establishment", "category"]:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
         instance.save()
         return instance
      
   def create(self, validated_data):
      owner =self.context['request'].user
      try:
         storeowner = Store.objects.create(owner=owner, **validated_data)
      except IntegrityError as e:
         # Catch the IntegrityError and customize the error message
         if 'duplicate key' in str(e).lower():
               raise ValidationError("You already have a store. Only one store per user is allowed.")
         else:
               raise e
      
      return storeowner
   
   def get_owner(self, value):
      if value:
         try:
            owner = CustomUser.objects.get(is_store_owner=True, id=value)
         except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User Does Not Exist or Is Not a Store Owner")
         return value
      if Store.objects.filter(owner=owner).exists:
         raise serializers.ValidationError("Sorry you have a store already")
      return serializers.ValidationError("Provide User")


class SizeSerializer(serializers.ModelSerializer):
   class Meta:
      model = Size
      fields = '__all__'


class PriceSerializer(serializers.ModelSerializer):
   class Meta:
      model = Price
      fields = ['size', 'price']


class BrandSerializer(serializers.ModelSerializer):
   class Meta:
      model = Brand
      fields = '__all__'


class SubCategorySerializer(serializers.ModelSerializer):
   class Meta:
      model = SubCategories
      fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
   class Meta:
      model = Category
      fields = '__all__'


class ProductTypesSerializer(serializers.ModelSerializer):
   class Meta:
      model = ProductTypes
      fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
   class Meta:
      model = ProductImage
      fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
   category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
   sizes = serializers.PrimaryKeyRelatedField(many=True, queryset=Size.objects.all())
   subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
   brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
   
   class Meta:
      model = Product
      fields = ['id', 'sku', 'name', 'description', 'quantity', 'color', 
               'is_available', 'created_at', 'on_promo', 'upload_status', 'sizes',  'category', 'subcategory', 'brand', 'images', ]
      read_only_fields = ('id', "sku")
   
   def to_representation(self, instance):
      cache_key = f"product_data_{instance.sku}"
      cached_data = cache.get(cache_key)
      
      if cached_data is not None:
         return cached_data
      
      representation = super(ProductSerializer, self).to_representation(instance)
      representation['created_at'] = instance.formatted_created_at()
      
      if representation['description'] is None:
         del representation['description']
         
      if representation['images'] is None:
         del representation['images']
      
      representation['sizes'] = [{"id": sizes.id, "name": sizes.name, "available":sizes.available} 
                                 for sizes in instance.sizes.all()]
      
      representation['brand'] = {"id": instance.brand.id,
                                 "name": instance.brand.name}
      
      representation['category'] = {"id": instance.category.id,
                                 "name": instance.category.name}
      
      representation['subcategory'] = {"id": instance.subcategory.id,
                                       "name": instance.subcategory.name}
      
      representation['images'] = [{"url": prod.image.url} 
                                 for prod in instance.images.all()]
      
      # representation['listed'] = [instance.list_product]

      cache.set(cache_key, representation, timeout= 60 * 10) #Cache product data for 10 mins
      return representation
   
   
   
   # serializers.py
class MarketPlaceSerializer(serializers.ModelSerializer):
   store = serializers.UUIDField(source='store_id', read_only=True)  # Add this line

   class Meta:
      model = MarketPlace
      fields = ("id", "store", "product")
      
      
   def create(self, validated_data):
      product_id = validated_data["product"]
      product = get_object_or_404(Product, id=product_id)
      # product.list_product = True
      product.save()

      store_id = self.context['request'].query_params.get('store')
      try:
         store = Store.objects.get(id=store_id)
      except Store.DoesNotExist:
         raise ValidationError(f'Store {store_id} does not exist.')

      validated_data['store'] = store  # Set the store field in validated_data

      # Create the MarketPlace instance
      instance = MarketPlace.objects.create(**validated_data, list_product=True)
      return instance

   def to_representation(self, instance):
      representation = super(MarketPlaceSerializer, self).to_representation(instance)
      representation['store'] = instance.store.name
      representation['product'] = instance.product.name
      representation['listed'] = instance.list_product
      return representation
   
   
# class MarketPlaceSerializer(serializers.ModelSerializer):
#    class Meta:
#       model = MarketPlace
#       fields = ("id", "store", "product")

#    def create(self, validated_data):
#       # Retrieve the product instance and modify it
#       product_id = validated_data["product"]
#       product = get_object_or_404(Product, id=product_id)
#       product.list_product = True  # Assuming 'list_product' is a boolean field
#       product.save()

#       store_id = self.context['request'].query_params.get('store')
#       try:
#          store = Store.objects.get(id=store_id)
#       except Store.DoesNotExist:
#          raise ValidationError(f'Store {store_id} does not exist.')

#       # Create the MarketPlace instance
#       instance = MarketPlace.objects.create(list_product=True, store=store, **validated_data)
#       return instance
   
#    def to_representation(self, instance):
#       representation = super(MarketPlaceSerializer, self).to_representation(instance)
#       representation['store'] = instance.store.name
#       representation['product'] = instance.product.name
#       representation['listed'] = instance.list_product
#       return representation