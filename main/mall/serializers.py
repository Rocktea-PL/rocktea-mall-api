from rest_framework.serializers import (
   ModelSerializer, 
   PrimaryKeyRelatedField, 
   ReadOnlyField,
   )

from workshop.exceptions import (
   ValidationError, 
   AuthenticationFailedError, 
   NotFoundError
   )

from .models import (
   CustomUser, 
   Store, 
   Category, 
   SubCategories, 
   Product, 
   Brand, 
   ProductTypes, 
   ProductImage, 
   MarketPlace, 
   ProductVariant, 
   Wallet, 
   StoreProductPricing, 
   ServicesBusinessInformation, 
   ReportUser,
   Notification,
   PromoPlans,
   BuyerBehaviour,
   ShippingData,
   ProductReview,
   DropshipperReview,
   ProductRating
   )

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re, logging
from PIL import Image
from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.core.cache import cache
from setup.celery import app
from django.db.models import Q
from order.models import PaystackWebhook
from mall.payments.verify_payment import verify_paystack_transaction
from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import urlparse
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from .store_features.get_store_id import get_store_instance

logger = logging.getLogger(__name__)

class LogisticSerializer(ModelSerializer):
   class Meta:
      model=CustomUser
      fields = ("id", "first_name", "last_name", "email", "profile_image", "password")
      
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
      user.is_logistics = True
      if password:
         # Set and save the user's password only if a valid password is provided
         user.set_password(password)
         user.save()
      return user

class OperationsSerializer(ModelSerializer):
   class Meta:
      model = CustomUser
      fields = ("id", "first_name", "last_name", "email", "profile_image", "password")

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
      user.is_operations = True

      if password:
         # Set and save the user's password only if a valid password is provided
         user.set_password(password)
         user.save()
      return user

class StoreOwnerSerializer(ModelSerializer):
   shipping_address = serializers.CharField(required=False, max_length=500)
   profile_image = serializers.FileField(required=False)
   
   class Meta:
      model=CustomUser
      fields = ("id", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_store_owner", "completed_steps", "password", "shipping_address")
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
      user.is_active = False

      if password:
         # Set and save the user's password only if a valid password is provided
         user.set_password(password)
         user.save()

      token_generator = PasswordResetTokenGenerator()
      token = token_generator.make_token(user)
      user.verification_token = token
      user.verification_token_created_at = timezone.now()
      user.save(update_fields=['verification_token', 'verification_token_created_at']) # Save token fields

      request = self.context.get("request")
      current_site = get_current_site(request).domain if request else "yourockteamall.com"
      protocol = request.scheme if request else "https"
      domain_name = f"{protocol}://{current_site}"
      verify_email_url = f"{domain_name}/verify-email?token="+str(token)

      # Fallback to referer for better frontend targeting
      if request:
         referer = request.META.get("HTTP_REFERER", "")
         if referer and 'swagger' not in referer.lower():
            parsed_referer = urlparse(referer)
            domain_name = f"{parsed_referer.scheme}://{parsed_referer.hostname}"
            verify_email_url = f"{domain_name}/verify-email?token={token}"

      # Send welcome email
      try:
         from setup.utils import sendEmail  # Import inside function to avoid circular imports
         subject = "Welcome to Rocktea Mall - Your Dropshipping Journey Begins!"
         context = {
            'full_name': user.get_full_name() or user.email, # Pass full_name or email
            'confirmation_url': verify_email_url,
            'current_year': timezone.now().year,
         }
         sendEmail(
            recipientEmail=user.email,
            template_name='emails/dropshippers_welcome.html',
            context=context,
            subject=subject,
            tags=["user-onboarding", "email-verification"]
         )
      except Exception as e:
         # Log but don't prevent user creation
         print(f"Failed to send welcome email: {str(e)}")
         logger.error(f"Failed to send user welcome email to {user.email}: {str(e)}")
         logger.error(f"Email error to {user.email}: {type(e).__name__} - {str(e)}")
         print(f"Email error to {user.email}: {type(e).__name__} - {str(e)}")

      return user
   
   def update(self, instance, validated_data):
      # Check if a new profile_image is being provided
      new_profile_image = validated_data.get('profile_image')

      # If a new image is provided AND it's different from the current one
      # OR if the client is sending null to clear the image
      if 'profile_image' in validated_data and new_profile_image != instance.profile_image:
         # Check if there was an old image to delete
         if instance.profile_image:
            try:
               # Calling .delete() on the FieldFile instance should trigger Cloudinary deletion
               # because cloudinary-storage hooks into this.
               instance.profile_image.delete()
            except Exception as e:
               # Log or handle the error gracefully, but don't prevent the update from proceeding
               print(f"Cloudinary deletion error during profile image update: {e}")
      
      # Handle password update separately as set_password doesn't go through setattr
      password = validated_data.pop('password', None)
      if password:
         if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', password):
            raise ValidationError({"error":"Passwords must include at least one special symbol, one number, one lowercase letter, and one uppercase letter."})
         instance.set_password(password)
      
      # Update other fields passed in validated_data
      for attr, value in validated_data.items():
         setattr(instance, attr, value)
      
      instance.save()
      return instance

   def to_representation(self, instance):
      representation = super().to_representation(instance)
      # Remove the password from the serialized output
      representation.pop('password', None)
      return representation

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
   @classmethod
   def get_token(cls, user):
      token = super().get_token(user)
      token['email'] = user.email
      return token

   def validate(self, attrs):
      data = super().validate(attrs)
      user = self.user  # Already authenticated user from parent class

      # Get user with permissions (allow all valid users)
      try:
         user = CustomUser.objects.get(id=user.id)
      except CustomUser.DoesNotExist:
         raise ValidationError("User Does Not Exist")
      except CustomUser.MultipleObjectsReturned:
         raise ValidationError("Multiple users found - database inconsistency")

      # Initialize store-related variables
      has_store = False
      store_id = None
      theme = None
      category = None
      domain_name = None
      completed = False
      has_made_payment = False

      # Only check for store if user is a store owner
      if user.is_store_owner:
         has_store = Store.objects.filter(owner=user).exists()
         
         if has_store:
            store = Store.objects.get(owner=user)
            
            # Enforce completed=True when payment exists
            if store.has_made_payment:
                store.completed = True
                store.save(update_fields=['completed'])
            
            # Update store-related variables
            store_id = store.id
            theme = store.theme
            category = store.category.id if store.category else None
            domain_name = store.domain_name
            completed = store.completed
            has_made_payment = store.has_made_payment
            
            # Payment verification
            try:
                paystack_payment = PaystackWebhook.objects.get(
                    user=user,
                    purpose="dropshipping_payment"
                )
                
                if paystack_payment.status == 'Pending':
                    payment_data = verify_paystack_transaction(paystack_payment.reference)
                    if payment_data and payment_data.get('data', {}).get('status') == 'success':
                        paystack_payment.status = 'Success'
                        paystack_payment.data = payment_data
                        paystack_payment.save()
                        store.has_made_payment = True
                        store.completed = True
                        store.save(update_fields=['has_made_payment', 'completed'])
                        has_made_payment = True
                        completed = True

            except PaystackWebhook.DoesNotExist:
                pass

      # Service check
      has_service = ServicesBusinessInformation.objects.filter(user=user).exists() if user.is_services else False

      # Build user data
      user_data = {
         "id": user.id,
         "first_name": user.first_name,
         "last_name": user.last_name,
         "email": user.email,
         "username": user.username,
         "contact": f"{user.contact}",
         "is_storeowner": user.is_store_owner,
         "has_store": has_store,
         "is_services": user.is_services,
         "is_logistics": user.is_logistics,
         "is_operations": user.is_operations,
         "has_service": has_service,
         "store_id": store_id,
         "theme": theme,
         "category": category,
         "domain_name": domain_name,
         "completed": completed,
         "hasMadePayment": has_made_payment
      }

      if user.is_services:
         user_data["type"] = user.type

      refresh = self.get_token(user)
      user_data["refresh"] = str(refresh)
      user_data["access"] = str(refresh.access_token)
      data['user_data'] = user_data
      return data

class CreateStoreSerializer(serializers.ModelSerializer):
    TIN_number = serializers.IntegerField(required=False)
    logo = serializers.FileField(required=False)
    year_of_establishment = serializers.DateField(required=False)

    class Meta:
        model = Store
        fields = ("id", "owner", "name", "TIN_number", "logo", "year_of_establishment", "category", 
                 "domain_name", "theme", "card_elevation", "background_color", "patterns", "color_gradient", 
                 "button_color", "card_elevation", "card_view", "card_color", "facebook", "whatsapp", "twitter", 
                 "instagram")
        extra_kwargs = {
            "background_color": {"required": False},
            "patterns": {"required": False},
            "color_gradient": {"required": False},
            "button_color": {"required": False},
            "card_elevation": {"required": False},
            "card_view": {"required": False},
        }
        read_only_fields = ("owner", "domain_name")  # domain_name is now read-only

    def validate_TIN_number(self, value):
        if isinstance(value, str) and len(value) != 9:
            raise ValidationError("Invalid TIN number. It should be 9 characters long.")
        return value

    def validate_logo(self, value):
        if value:
            file_extension = value.name.split('.')[-1].lower()
            if file_extension not in ['png']:
                raise ValidationError("Invalid Image format. Only PNG is allowed.")
        return value
        
    def validate_owner(self, value):
        if value is None:
            return value

        try:
            user = CustomUser.objects.get(is_store_owner=True, id=value)
        except CustomUser.DoesNotExist:
            raise ValidationError("User with ID {} does not exist or is not a store owner.".format(value))
        return value
    
    def validate_name(self, value):
        """Validate store name for DNS compatibility"""
        if len(value.strip()) < 2:
            raise ValidationError("Store name must be at least 2 characters long.")
        
        # Check for existing store with same name
        if self.instance:  # Update case
            if Store.objects.filter(name=value).exclude(id=self.instance.id).exists():
                raise ValidationError("A store with this name already exists.")
        else:  # Create case
            if Store.objects.filter(name=value).exists():
                raise ValidationError("A store with this name already exists.")
        
        return value
    
    def update(self, instance, validated_data):
        # Remove domain_name from validated_data if present (it's read-only)
        validated_data.pop('domain_name', None)
        
        for field in ["name", "TIN_number", "logo", "year_of_establishment", "category", "theme", 
                     "card_elevation", "background_color", "patterns", "color_gradient", "button_color", 
                     "card_view", "facebook", "whatsapp", "twitter", "instagram"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance

    def create(self, validated_data):
        owner = self.context['request'].user
        
        # Check if user already has a store
        if Store.objects.filter(owner=owner).exists():
            raise ValidationError("You already have a store. Only one store per user is allowed.")

        try:
            store = Store.objects.create(owner=owner, **validated_data)
        except IntegrityError as e:
            if 'duplicate key' in str(e).lower():
                raise ValidationError("You already have a store. Only one store per user is allowed.")
            else:
                raise NotFoundError("An error occurred while creating the store. Please try again later.")

        return store

class ProductRatingSerializer(serializers.ModelSerializer):
   class Meta:
      model = ProductRating
      fields = ("product", "star")
      
   def to_representation(self, instance):
      representation = super(ProductRatingSerializer, self).to_representation(instance)
      representation["product"] = instance.product.name
      return representation

class BrandSerializer(serializers.ModelSerializer):
   class Meta:
      model = Brand
      fields = '__all__'

   def validate_name(self, value):
      # Check if brand name already exists (for updates)
      if self.instance and self.instance.name != value:
         if Brand.objects.filter(name=value).exists():
               raise serializers.ValidationError("A brand with this name already exists.")
      elif not self.instance and Brand.objects.filter(name=value).exists():
         raise serializers.ValidationError("A brand with this name already exists.")
      return value

class SubCategorySerializer(serializers.ModelSerializer):
   category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), read_only=False)

   class Meta:
      model = SubCategories
      fields = '__all__'

   def validate(self, data):
      # Check for unique subcategory name within the same category
      category = data.get('category')
      name = data.get('name')
      
      if category and name:
         query = SubCategories.objects.filter(category=category, name=name)
         if self.instance:
            query = query.exclude(pk=self.instance.pk)
         
         if query.exists():
            raise serializers.ValidationError(
               "A subcategory with this name already exists in this category."
            )
      
      return data
      
   # def to_representation(self, instance):
   #    representation = super(SubCategorySerializer, self).to_representation(instance)
   #    representation['category'] = {'id': instance.category.id, 'name': instance.category.name}
   #    return representation

class CategorySerializer(serializers.ModelSerializer):
   class Meta:
      model = Category
      fields = '__all__'

   def validate_name(self, value):
      # Check if category name already exists (for updates)
      if self.instance and self.instance.name != value:
         if Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
      elif not self.instance and Category.objects.filter(name=value).exists():
         raise serializers.ValidationError("A category with this name already exists.")
      return value

class ProductTypesSerializer(serializers.ModelSerializer):
   subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
   class Meta:
      model = ProductTypes
      fields = '__all__'

   def validate(self, data):
      # Check for unique product type name within the same subcategory
      subcategory = data.get('subcategory')
      name = data.get('name')
      
      if subcategory and name:
         query = ProductTypes.objects.filter(subcategory=subcategory, name=name)
         if self.instance:
            query = query.exclude(pk=self.instance.pk)
         
         if query.exists():
            raise serializers.ValidationError(
               "A product type with this name already exists in this subcategory."
            )
      
      return data
      
   # def to_representation(self, instance):
   #    representation = super(ProductTypesSerializer, self).to_representation(instance)
   #    representation['subcategory'] = {'id': instance.subcategory.id, 'name': instance.subcategory.name}
   #    return representation

class ProductImageSerializer(serializers.ModelSerializer):
   class Meta:
      model = ProductImage
      fields = ['id', 'images']

   def get_url(self, obj):
      if obj.images:
         return obj.images.url
      return None

class ProductVariantSerializer(serializers.ModelSerializer):
   wholesale_price = serializers.DecimalField(max_digits=11, decimal_places=2)
   size = serializers.CharField(required=False)
   product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True)
   
   class Meta:
      model = ProductVariant
      fields = '__all__'
      
   def to_representation(self, instance):
      # Call the parent class's to_representation method
      representation = super(ProductVariantSerializer, self).to_representation(instance)

      # Format the 'total_price' field with commas as thousands separator
      representation['wholesale_price'] = '{:,.2f}'.format(instance.wholesale_price)

      return representation

class StoreProductPricingSerializer(serializers.ModelSerializer):
   product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
   retail_price = serializers.DecimalField(max_digits=11, decimal_places=2)

   class Meta:
      model = StoreProductPricing
      fields = ['id', 'store', 'product', 'retail_price']

   def to_representation(self, instance):
      representation = super().to_representation(instance)
      representation['product'] = {"id": getattr(instance.product, 'id', None), "name": getattr(instance.product, 'name', None)}
      representation['store'] = {"id": instance.store.id, "name": instance.store.name}
      retail_price_float = float(instance.retail_price)
      representation['retail_price'] = '{:,.2f}'.format(retail_price_float)
      return representation

class ProductSerializer(serializers.ModelSerializer):
   category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
   subcategory = serializers.PrimaryKeyRelatedField(queryset=SubCategories.objects.all())
   brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
   producttype = serializers.PrimaryKeyRelatedField(queryset=ProductTypes.objects.all())
   product_variants = ProductVariantSerializer(read_only=True, many=True)
   store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all(), many=True, required=False)
   
   class Meta:
      model = Product
      fields = ['id', 'sku', 'name', 'description', 'quantity', 
               'is_available', 'created_at', 'on_promo', 'upload_status', 'category', 'subcategory', 
               'brand', "producttype",'images', "product_variants", 'store']
      read_only_fields = ('id', "sku")
      extra_kwargs = {
         'size': {'required': False}
      }
   
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

      representation['sales_count'] = {"sales_count": instance.sales_count}

      representation['category'] = {"id": instance.category.id,
                                 "name": instance.category.name}

      representation['subcategory'] = {"id": instance.subcategory.id,
                                       "name": instance.subcategory.name}
      
      representation['producttype'] = instance.producttype.name

      representation['images'] = [{"url": prod.images.url} for prod in instance.images.all()]

      cache.set(cache_key, representation, timeout=60 * 5)  # Cache product data for 5 mins
      return representation

class SimpleProductSerializer(serializers.ModelSerializer):
   unit_sold = serializers.SerializerMethodField()
   price = serializers.SerializerMethodField()
   date = serializers.SerializerMethodField()

   class Meta:
      model = Product
      fields = ['id', 'name', 'unit_sold', 'sku', 'price', 'date']

   def get_unit_sold(self, obj):
      return getattr(obj.sales_count, 'sales_count', 0)

   def get_price(self, obj):
      store = self.context.get('store')
      if not store:
         return None  # Store context is missing
      try:
         pricing = StoreProductPricing.objects.get(product=obj, store=store)
         return "{:.2f}".format(pricing.retail_price)
      except StoreProductPricing.DoesNotExist:
         return None
      except Exception as e:
         # Log the error for debugging
         print(f"Error fetching price: {e}")
         return None

   def get_date(self, obj):
      return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

class ServicesBusinessInformationSerializer(serializers.ModelSerializer):
   class Meta:
      model = ServicesBusinessInformation
      fields = "__all__"

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
            price = StoreProductPricing.objects.get(product=product, size=size_id).retail_price
            product_prices[size_id] = price
         except StoreProductPricing.DoesNotExist:
            logging.error("An Error Unexpectedly Occurred")
      return product_prices
   
   def create(self, validated_data):
      product_id = self.context['request'].query_params.get('product')
      try:
         product = Product.objects.get(id=product_id)
         # Assign the product to the instance
         validated_data['product'] = product
      except Product.DoesNotExist:
         raise ValidationError("Product not found.")

      store = self.get_store_instance()
      validated_data['store'] = store  # Set the store field in validated_data

      # Check if a Marketplace instance already exists for the given product and store
      marketplace_instance = MarketPlace.objects.filter(product=product, store=store).first()

      if marketplace_instance:
         # Update the existing instance if it already exists
         marketplace_instance.list_product = True  # Assuming you want to set list_product to True
         marketplace_instance.save()
         return marketplace_instance
      else:
         # Create a new Marketplace instance if it doesn't exist
         instance = MarketPlace.objects.create(**validated_data, list_product=True)
         return instance

   def get_store_instance(self):
      """ Use Store Domain Name to get the Store instance"""
      store_domain = self.context['request'].domain_name
      try:
         store = Store.objects.get(id=store_domain)
      except Store.DoesNotExist:
         raise ValidationError("Store Does Not Exist")
      return store

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
               "quantity": instance.product.quantity,
               "images": self.serialize_product_images(instance.product.images.all()),
               "product_variant": self.serialize_product_variants(instance.product.product_variants.all()),
               "category": instance.product.category.name,
               "subcategory": instance.product.subcategory.name,
               "producttype": instance.product.producttype.name,
               "upload_status": instance.product.upload_status
         }
      else:
         # Handle the case where product is None
         representation['product'] = None

      representation['listed'] = instance.list_product
      cache.set(cache_key, representation, timeout=60 * 5)
      return representation

   def serialize_product_images(self, images):
      return [{"id": image.id, "url": image.images.url if image.images else None} for image in images]
   
   # Add this method to serialize product variants
   def serialize_product_variants(self, variants):
      return [{"id": variant.id, "size": variant.size, "color": variant.colors, "wholesale_price": variant.wholesale_price} for variant in variants]

class ProductDetailSerializer(serializers.ModelSerializer):
   class Meta:
      model = Product
      fields = '__all__'
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
      # representation['producttype'] = {"id": instance.producttype.id, "name": instance.producttype.name}

      representation['product'] = {
            "id": instance.id,
            "name": instance.name,
            "images": [{"url": prod.images.url} for prod in instance.images.all()],
            "product_variant": self.serialize_product_variants(instance.product_variants.all()),
            "category": instance.category.name,
            "subcategory": instance.subcategory.name,
            # "producttype": getattr(instance.producttypes, 'name', None),
            "upload_status": instance.upload_status
         }
      cache.set(cache_key, representation, timeout=60 * 5)
      return representation

   def serialize_product_variants(self, variants):
      return [{"id": variant.id, "size": variant.size, "color": variant.colors, "wholesale_price": variant.wholesale_price} for variant in variants]

class WalletSerializer(serializers.ModelSerializer):
   class Meta:
      model = Wallet
      fields = ['id', 'store', 'balance', 'account_name', 'pending_balance', 'balance', 'nuban', 'bank_code']
      

   def to_representation(self, instance):
      representation = super(WalletSerializer, self).to_representation(instance)
      representation['store'] = {"id": instance.store.id, "name": instance.store.name}
      return representation

class ReportUserSerializer(serializers.ModelSerializer):
   other = serializers.CharField(required=False)
   support_code = serializers.CharField(read_only=True)
   status = serializers.CharField(read_only=True)
   class Meta:
      model = ReportUser
      fields = ['id', 'user', 'title', 'other', 'details', 'support_code', 'status']
      
   def to_representation(self, instance):
      representation = super(ReportUserSerializer, self).to_representation(instance)
      representation['user'] = {
         "id": instance.user.id,
         "full_name": f"{instance.user.first_name} {instance.user.last_name}",
      }
      return representation

class NotificationSerializer(serializers.ModelSerializer):
   class Meta:
      model = Notification
      fields = ['id', 'recipient', 'store', 'message', 'created_at', 'read']
      
class PromoPlanSerializer(serializers.ModelSerializer):
   class Meta:
      model = PromoPlans
      fields = ['id', 'purpose', 'store', 'category', 'code']

# Pre-Structure for Data Analyst
class BuyerBehaviourSerializer(serializers.ModelSerializer):
   class Meta:
      model = BuyerBehaviour
      fields = "__all__"
    
class ShippingDataSerializer(serializers.ModelSerializer):
   class Meta:
      model = ShippingData
      fields = "__all__"
  
class ProductReviewSerializer(serializers.ModelSerializer):
   class Meta:
      model = ProductReview
      fields = "__all__"
      
   def to_representation(self, instance):
      representation = super(ProductReviewSerializer, self).to_representation(instance)
      representation['user'] = f"{instance.user.first_name} {instance.user.last_name}"
      representation['product'] = instance.product.name
      return representation

class DropshipperReviewSerializer(serializers.ModelSerializer):
   class Meta:
      model = DropshipperReview
      fields = "__all__"
      
   def to_representation(self, instance):
      representation = super(DropshipperReviewSerializer, self).to_representation(instance)
      representation['user'] = f"{instance.user.first_name} {instance.user.last_name}"
      return representation

class ResetPasswordEmailRequestSerializer(serializers.Serializer):
   email = serializers.EmailField()

class ResetPasswordConfirmSerializer(serializers.Serializer):
   token = serializers.CharField()
   password = serializers.CharField()