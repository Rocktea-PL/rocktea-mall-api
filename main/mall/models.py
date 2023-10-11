from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from uuid import uuid4
import random
import string
from phonenumber_field.modelfields import PhoneNumberField
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from .validator import YearValidator
from multiselectfield import MultiSelectField


def generate_unique_code():
   return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
      # Create a standard user
      if not email:
         raise ValueError('The Email field must be set')
      email = self.normalize_email(email)
      user = self.model(email=email, **extra_fields)
      user.set_password(password)
      user.save(using=self._db)
      return user

    def create_superuser(self, email, password=None, **extra_fields):
      # Create a superuser
      extra_fields.setdefault('is_staff', True)
      extra_fields.setdefault('is_superuser', True)

      if extra_fields.get('is_staff') is not True:
         raise ValueError('Superuser must have is_staff=True.')
      if extra_fields.get('is_superuser') is not True:
         raise ValueError('Superuser must have is_superuser=True.')

      return self.create_user(email, password, **extra_fields)


# StoreOwner models
class CustomUser(AbstractUser):
   id = models.CharField(default=uuid4, unique=True, primary_key=True, db_index=True, max_length=36)
   username = models.CharField(max_length=7, unique=True)
   email = models.EmailField(unique=True)
   first_name = models.CharField(max_length=250)
   last_name = models.CharField(max_length=250)
   contact = PhoneNumberField()
   is_store_owner = models.BooleanField(default=False)
   is_consumer = models.BooleanField(default=False)
   password = models.CharField(max_length=200)
   associated_domain = models.ForeignKey("Store", on_delete=models.CASCADE, null=True)
   profile_image = models.FileField(storage=RawMediaCloudinaryStorage)

   USERNAME_FIELD = 'email'
   REQUIRED_FIELDS = []

   objects = CustomUserManager()
   
   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         models.Index(fields=['id'], name='id_idx'),
      ]
   
   def save(self, *args, **kwargs):
      if not self.username:
         self.username = self._generate_unique_username()
      return super().save(*args, **kwargs)

   def _generate_unique_username(self):
      return "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=7))
   
   def __str__(self):
      return self.first_name
   

class Store(models.Model):
   id = models.CharField(max_length=36, default=uuid4, unique=True, db_index=True, primary_key=True)
   owner = models.OneToOneField(CustomUser, related_name="owners", on_delete=models.CASCADE, limit_choices_to={"is_store_owner": True})
   name = models.CharField(max_length=150, unique=True)
   email = models.EmailField(unique=True)
   TIN_number = models.IntegerField()
   logo = models.FileField(storage=RawMediaCloudinaryStorage)
   cover_image = models.FileField(storage=RawMediaCloudinaryStorage, null=True)
   year_of_establishment = models.DateField(validators=[YearValidator])
   category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True)
   
   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         models.Index(fields=['id'], name='store_id_idx'),
      ]
      
   def __str__(self):
      return self.name




class StoreActivationInfo(models.Model):
   PAYMENT_STATUS = (
      ('PD', 'Paid'),
      ('UP', 'Unpaid'),
   )
   
   DOMAIN_ACTIVATION_STATUS = (
      ('ACTIVATED', 'ACTIVATED'),
      ('DISACTIVATED', 'DISACTIVATED'),
      ('UNPROCESSED', 'UNPROCESSED'),
      ('UNDER-REVIEW', 'UNDER-REVIEW')
   )
   user = models.OneToOneField(CustomUser, limit_choices_to={"is_store_owner":True}, on_delete=models.CASCADE)
   store = models.OneToOneField(Store, on_delete=models.CASCADE)
   chosen_domain_name = models.CharField(max_length=20, unique=True)
   amount_paid = models.CharField(max_length=10, editable=False)
   status = models.CharField(max_length=12, choices=DOMAIN_ACTIVATION_STATUS, default='UNPROCESSED')
   payment_status = models.CharField(max_length=6, choices=PAYMENT_STATUS, default='UP')
   payment_reference = models.CharField(max_length=30, unique=True)
   
   def __str__(self):
      return f'{self.store.name} {self.domain_activation}'


class Product(models.Model):
   COLORS = (
      ('Red', 'Red'),
      ('Yellow', 'Yellow'),
      ('Blue', 'Blue'),
      ('Green', 'Green'),
      ('Orange', 'Orange'),
      ('Purple', 'Purple'),
      ('Pink', 'Pink'),
      ('Brown', 'Brown'),
      ('Gray', 'Gray'),
      ('Black', 'Black'),
      ('White', 'White'),
      ('Beige', 'Beige'),
      ('Cyan', 'Cyan'),
      ('Magenta', 'Magenta'),
      ('Lavender', 'Lavender'),
      ('Teal', 'Teal'),
      ('Navy', 'Navy'),
      ('Olive', 'Olive'),
      ('Maroon', 'Maroon'),
      ('Turquoise', 'Turquoise'),
      ('Indigo', 'Indigo'),
      ('Violet', 'Violet'),
      ('Gold', 'Gold'),
      ('Silver', 'Silver'),
      ('Bronze', 'Bronze'),
      ('Nude', 'Nude'),
      ('Neutral', 'Neutral'),
      ('Berge', 'Berge'),
      ('Ivory', 'Ivory'),
      ('Metallic', 'Metallic'),
      ('Grow', 'Grow'),
      ('Multi', 'Multi'),
      ('Clear', 'Clear'),
      ('Burgundy', 'Burgundy'),
      ('Rose Gold', 'Rose Gold'),
   )
   
   UPLOAD_STATUS = (
      ("Approved", "Approved"),
      ("Pending", "Pending"),
      ("Rejected", "Rejected")
   )

   sn = models.CharField(max_length=5, unique=True, blank=True)
   sku = models.CharField(max_length=8, unique=True, blank=True)
   name = models.CharField(max_length=50)
   description = models.TextField(null=True)
   quantity = models.IntegerField()
   color = models.CharField(choices=COLORS, max_length=9, null=True, blank=True)
   category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True)
   subcategory = models.ForeignKey('SubCategories', on_delete=models.CASCADE, null=True)
   brand = models.ForeignKey('Brand', on_delete=models.CASCADE, null=True)
   created_at=models.DateTimeField(auto_now_add=True, null=True)
   on_promo = models.BooleanField(default=False)
   is_available = models.BooleanField(default=True)
   upload_status = models.CharField(max_length=8, choices=UPLOAD_STATUS, null=True, default="Pending")
   sizes = models.ManyToManyField('Size', through='Price')
   images = models.ManyToManyField('ProductImage')
   
   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         models.Index(fields=['sn'], name='product_sn_snx'),
         models.Index(fields=['sku'], name='product_sku_skux'),
      ]
      
   
   
   def formatted_created_at(self):
      # Format the created_at field as "YMD, Timestamp"
      return self.created_at.strftime("%Y-%m-%d, %H:%M%p")
   
   def save(self, *args, **kwargs):
      if not self.sn:
         self.sn = generate_unique_code()
      if not self.sku:
         self.sku = self._generate_sku()
      return super().save(*args, **kwargs)
   
   def _generate_sku(self):
      return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
      
   def __str__(self):
      return self.sn


class ProductImage(models.Model):
   image = models.FileField(storage=RawMediaCloudinaryStorage)
   
   class Meta:
      indexes = [
         models.Index(fields=['image'], name='product_images_imagesx')
      ]

# class MarketPlace(models.Model):
#    store = models.

class Category(models.Model):
   CHOICES = (
      ("Phone and Tablet", "Phone and Tablet"),
      ("Men's Fashion", "Men's Fashion"),
      ("Women's Fashion", "Women's Fashion"),
      ("Mobile Accessories", "Mobile Accessories"),
      ("Electronics", "Electronics"),
      ("Health & Beauty", "Health & Beauty"),
      ("Kids", "Kids"),
      ("Sporting", "Sporting"),
      ("Computing", "Computing"),
      ("Groceries", "Groceries"),
      ("Video Games", "Video Games"),
      ("Home & Office", "Home & Office"),
      
   )
   name = models.CharField(choices=CHOICES, unique=True, max_length=18)
   
   class Meta:
      indexes = [
         models.Index(fields=['name'], name='category_name_namex')
      ]
   
   def __str__(self):
      return self.name


class SubCategories(models.Model):
   category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
   name = models.CharField(max_length=30)
   
   class Meta:
      indexes = [
         models.Index(fields=['name'], name='subcategories_name_namex')
      ]
   
   def __str__(self):
      return self.name
   

class ProductTypes(models.Model):
   subcategory = models.ForeignKey(SubCategories, related_name="producttypes", on_delete=models.CASCADE)
   name = models.CharField(max_length=100, unique=True)
   
   class Meta:
      indexes = [
         models.Index(fields=['name'], name='producttypes_name_namex')
      ]
   
   def __str__(self):
      return self.name
   

class Brand(models.Model):
   producttype = models.ManyToManyField(ProductTypes)
   name = models.CharField(max_length=25, unique=True)
   
   class Meta:
      indexes = [
         models.Index(fields=['name'], name='brand_name_namex')
      ]
   
   
   def __str__(self):
      return self.name
   

class Size(models.Model):
   name = models.CharField(max_length=10, null=True, blank=True)
   
   class Meta:
      indexes = [
         models.Index(fields=['name'], name='size_name_namex')
      ]
   
   def __str__(self):
      return self.name


class Price(models.Model):
   product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
   size = models.ForeignKey('Size', on_delete=models.CASCADE, null=True)
   price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
   
   class Meta:
      indexes = [
         models.Index(fields=['price'], name='price_price_pricex')
      ]
   
   def __str__(self):
      return f"{self.product.name} {self.size.name} - {self.price}"
   
   
class AccountDetails(models.Model):
   user = models.OneToOneField(CustomUser, limit_choices_to={"is_store_owner":True}, on_delete=models.CASCADE)
   account_name = models.CharField(max_length=300)
   nuban = models.CharField(max_length=10, unique=True)
   bank_code = models.IntegerField()
   
   def __str__(self):
      return f"{user.first_name}"
   
   
class Wallet(models.Model):
   balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   pending_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   paid = models.BooleanField(default=False)
