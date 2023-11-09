from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ReadOnlyField, ValidationError
from .models import (CustomUser, Store, Category, SubCategories, Product, Brand, ProductTypes, 
                     ProductImage, MarketPlace, ProductVariant, StoreProductVariant)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re, logging
from PIL import Image
from rest_framework import status
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.core.cache import cache
from setup.celery import app
from django.http import Http404


class StoreOwnerSerializer(ModelSerializer):
   shipping_address = serializers.CharField(required=False, max_length=500)
   
   class Meta:
      model=CustomUser
      fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_store_owner","password", "shipping_address")
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
            "has_store": has_store,
            "store_id": self.user.owners.id
            }
      
      refresh = self.get_token(self.user)
      data["refresh"] = str(refresh)
      data["access"] = str(refresh.access_token)
      return data


class CreateStoreSerializer(serializers.ModelSerializer):
   TIN_number = serializers.IntegerField(required=False)
   logo = serializers.FileField(required=False)
   year_of_establishment = serializers.DateField(required=False)

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

class ProductVariantSerializer(serializers.ModelSerializer):
   # size_name = serializers.SerializerMethodField()
   class Meta:
      model = ProductVariant
      fields = '__all__'
      

class StoreProductVariantSerializer(serializers.ModelSerializer):
   productvariant = ProductVariantSerializer(many=True, read_only=True)
   
   class Meta:
      model = StoreProductVariant
      fields = '__all__'
      

class ProductSerializer(serializers.ModelSerializer):
   category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
   # sizes = serializers.PrimaryKeyRelatedField(many=True, queryset=Size.objects.all())
   subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
   brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
   producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
   storevariant = StoreProductVariantSerializer(read_only=True)
   product_variants = ProductVariantSerializer(read_only=True, many=True)
   
   class Meta:
      model = Product
      fields = ['id', 'sku', 'name', 'description', 'quantity', 
               'is_available', 'created_at', 'on_promo', 'upload_status', 'category', 'subcategory', 'brand', "producttype",'images', 'storevariant', "product_variants"]
      read_only_fields = ('id', "sku")
   
   def to_representation(self, instance):
      cache_key = f"product_data_{instance.name}"
      cached_data = cache.get(cache_key)
      
      if cached_data is not None:
         return cached_data
      
      representation = super(ProductSerializer, self).to_representation(instance)
      representation['created_at'] = instance.formatted_created_at()
      
      if representation['description'] is None:
         del representation['description']
         
      if representation['images'] is None:
         del representation['images']
      
      representation['brand'] = {"id": instance.brand.id,
                                 "name": instance.brand.name}
      
      # representation['producttype'] = {"name": instance.}
      
      representation['category'] = {"id": instance.category.id,
                                 "name": instance.category.name}
      
      representation['subcategory'] = {"id": instance.subcategory.id,
                                       "name": instance.subcategory.name}

      representation['images'] = [{"url": prod.images.url} for prod in instance.images.all()]

      cache.set(cache_key, representation, timeout=60)  # Cache product data for 10 mins
      return representation


# serializers.py
class MarketPlaceSerializer(serializers.ModelSerializer):
   store = serializers.UUIDField(source='store_id', read_only=True)
   # size = PriceSerializer(many=True, read_only=True)

   class Meta:
      model = MarketPlace
      fields = ("id", "store", "product")

   def get_product_price(self, product, size_ids):
      product_prices = {}
      for size_id in size_ids:
         try:
            price = Price.objects.get(product=product, size=size_id).price
            product_prices[size_id] = price
         except Price.DoesNotExist:
            logging.error("An Error Unexpectedly Occurred")
      return product_prices
            
   def create(self, validated_data):
      product_id = self.context['request'].query_params.get('product')
      try:
         product = get_object_or_404(Product, id=product_id)
         # Assign the product to the instance
         validated_data['product'] = product
      except Http404:
         raise ValidationError("Product not found.")

      store_id = self.context['request'].query_params.get('store')
      try:
         store = Store.objects.get(id=store_id)
      except Store.DoesNotExist:
         raise ValidationError(f'Store {store_id} does not exist.')

      validated_data['store'] = store  # Set the store field in validated_data

      # Create the MarketPlace instance
      instance = MarketPlace.objects.create(**validated_data, list_product=True)
      return instance
      
      # Assuming `product` is a related field
   def to_representation(self, instance):
      cache_key = f"Listed Product_{instance.id}"
      cached_data = cache.get(cache_key)
      
      if cached_data is not None:
         return cached_data
      
      representation = super().to_representation(instance)

   # Assuming `store` is a related field
      representation['store'] = {"id": instance.store.id, "name": instance.store.name}

      # Assuming `product` is a related field
      if instance.product:
            product = Product.objects.select_related("category", "subcategory").prefetch_related(
               "images", "product_variants"
            ).get(id=instance.product.id)
            instance.product = product
            representation['product'] = {
               "id": instance.product.id,
               "name": instance.product.name,
               "images": self.serialize_product_images(instance.product.images.all()),
               "product_variant": self.serialize_product_variants(instance.product.product_variants.all()),
               "store_variant": self.get_store_variant(instance.product.product_variants.all(), instance.store.id),
               "category": instance.product.category.name,
               "subcategory": instance.product.subcategory.name,
               "product_type": instance.product.producttype,
               "upload_status": instance.product.upload_status
         }
      else:
         # Handle the case where product is None
         representation['product'] = None

      representation['listed'] = instance.list_product
      cache.set(cache_key, representation, timeout=200)
      return representation

   def serialize_product_images(self, images):
      return [{"id": image.id, "url": image.images.url if image.images else None} for image in images]
   
   # Add this method to serialize product variants
   def serialize_product_variants(self, variants):
      return [{"id": variant.id, "size": variant.size, "color": variant.colors, "wholesale_price": variant.wholesale_price} for variant in variants]


   def get_store_variant(self, product_variants, store_id):
      product_variant_ids = [variant.id for variant in product_variants]
      store_variant_queryset = StoreProductVariant.objects.filter(
         store=store_id, product_variant__in=product_variant_ids
      ).select_related("product_variant")

      store_variants_details = []
      for store_variant_detail in store_variant_queryset:
         store_variants_details.append(
               {
                  "id": store_variant_detail.id,
                  "product_variant_id": store_variant_detail.product_variant.id,
                  "product_variant_size": store_variant_detail.product_variant.size,
                  "retail_price": store_variant_detail.retail_price,
               }
         )
      return store_variants_details
   
   
class ProductDetailSerializer(serializers.ModelSerializer):
   category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
   subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
   brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
   producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
   storevariant = StoreProductVariantSerializer(read_only=True)
   product_variants = ProductVariantSerializer(read_only=True, many=True)

   class Meta:
      model = Product
      fields = ['id', 'sku', 'name', 'description', 'quantity', 'is_available', 'created_at', 'on_promo',
               'upload_status', 'category', 'subcategory', 'brand', 'producttype', 'images', 'storevariant',
               'product_variants']
      read_only_fields = ('id', 'sku')

   def to_representation(self, instance):
      cache_key = f"product_data_{instance.name}"
      cached_data = cache.get(cache_key)

      if cached_data is not None:
         return cached_data

      representation = super(ProductDetailSerializer, self).to_representation(instance)
      representation['created_at'] = instance.formatted_created_at()

      if representation['description'] is None:
         del representation['description']

      if representation['images'] is None:
         del representation['images']

      representation['brand'] = {"id": instance.brand.id, "name": instance.brand.name}
      representation['category'] = {"id": instance.category.id, "name": instance.category.name}
      representation['subcategory'] = {"id": instance.subcategory.id, "name": instance.subcategory.name}

      representation['product'] = {
            "id": instance.id,
            "name": instance.name,
            "images": [{"url": prod.images.url} for prod in instance.images.all()],
            "product_variant": self.serialize_product_variants(instance.product_variants.all()),
            # "store_variant": self.get_store_variant(instance.product_variants.all()),
            "category": instance.category.name,
            "subcategory": instance.subcategory.name,
            "product_type": instance.producttype,
            "upload_status": instance.upload_status
         }
      # else:
      #    representation['product'] = None

      # representation['listed'] = instance.list_product
      cache.set(cache_key, representation, timeout=20)
      return representation

   def serialize_product_variants(self, variants):
      return [{"id": variant.id, "size": variant.size, "color": variant.colors, "wholesale_price": variant.wholesale_price} for variant in variants]

   def get_store_variant(self, product_variants, store_id):
      product_variant_ids = [variant.id for variant in product_variants]
      store_variant_queryset = StoreProductVariant.objects.filter(
         store=store_id, product_variant__in=product_variant_ids
      ).select_related("product_variant")

      store_variants_details = []
      for store_variant_detail in store_variant_queryset:
         store_variants_details.append(
               {
                  "id": store_variant_detail.id,
                  "product_variant_id": store_variant_detail.product_variant.id,
                  "product_variant_size": store_variant_detail.product_variant.size,
                  "retail_price": store_variant_detail.retail_price,
               }
         )
      return store_variants_details