from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from uuid import uuid4
import random
import string
from phonenumber_field.modelfields import PhoneNumberField
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from .validator import YearValidator
from multiselectfield import MultiSelectField
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver
# from services.models import ServicesCategory

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
   SERVICE_TYPE = (
      ('Personal Assistant', 'Personal Assistant'),
      ('Fashion Designer', 'Fashion Designer'),
      ('Makeup Artist', 'Makeup Artist'),
   )

   id = models.CharField(default=uuid4, unique=True, primary_key=True, db_index=True, max_length=36)
   username = models.CharField(max_length=7, unique=True)
   email = models.EmailField(unique=True)
   first_name = models.CharField(max_length=250)
   last_name = models.CharField(max_length=250)
   contact = PhoneNumberField()
   is_store_owner = models.BooleanField(default=False)
   is_consumer = models.BooleanField(default=False)
   is_logistics = models.BooleanField(default=False)
   is_operations = models.BooleanField(default=False)
   password = models.CharField(max_length=200)
   associated_domain = models.ForeignKey("Store", on_delete=models.CASCADE, null=True)
   profile_image = models.FileField(storage=RawMediaCloudinaryStorage)
   shipping_address = models.CharField(max_length=500, null=True)

   # Services Extension
   type = models.CharField(choices=SERVICE_TYPE, max_length=18, null=True)
   is_services = models.BooleanField(default=False)
   
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
   
   
class ServicesBusinessInformation(models.Model):
   EXPERIENCE = (
      ("1-2 Years", "1-2 Years"),
      ("3-4 Years", "3-4 Years"),
      ("5-6 Years", "5-6 Years"),
      ("7 Years & Above", "7 Years & Above")
   )
   user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
   name = models.CharField(max_length=150, unique=True)
   category = models.ForeignKey('services.ServicesCategory', on_delete=models.CASCADE, null=True)
   email = models.EmailField(unique=True)
   contact = models.CharField(unique=True, max_length=14)
   years_of_experience = models.CharField(max_length=15)
   about = models.TextField(max_length=100)
   location = models.CharField(max_length=250, null=True)
   business_photograph = models.FileField(storage=RawMediaCloudinaryStorage)
   business_photograph2 = models.FileField(storage=RawMediaCloudinaryStorage, null=True)
   business_photograph3 = models.FileField(storage=RawMediaCloudinaryStorage, null=True)
   charges = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)

   def __str__(self):
      return self.name


class Wallet(models.Model):
   store = models.OneToOneField('Store', on_delete=models.CASCADE, null=True)
   balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   account_name = models.CharField(max_length=300, null=True)
   pending_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   nuban = models.CharField(max_length=10, unique=True, null=True)
   bank_code = models.IntegerField(null=True)

   def __str__(self):
      return self.store.name


class Store(models.Model):
   id = models.CharField(max_length=36, default=uuid4, unique=True, db_index=True, primary_key=True)
   owner = models.OneToOneField(CustomUser, related_name="owners", on_delete=models.CASCADE, limit_choices_to={"is_store_owner": True})
   name = models.CharField(max_length=150, unique=True)
   email = models.EmailField(unique=True)
   TIN_number = models.BigIntegerField(null=True)
   logo = models.FileField(storage=RawMediaCloudinaryStorage, null=True)
   cover_image = models.FileField(storage=RawMediaCloudinaryStorage, null=True)
   year_of_establishment = models.DateField(validators=[YearValidator], null=True)
   category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True)
   domain_name = models.CharField(max_length=100, null=True, unique=True)
   
   completed = models.BooleanField(default=False)
   
   # Custom Add-Ons
   theme = models.CharField(max_length=6, null=True)
   facebook = models.URLField(null=True)
   whatsapp = models.URLField(null=True)
   instagram = models.URLField(null=True)
   twitter = models.URLField(null=True)
   
   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         models.Index(fields=['id'], name='store_id_idx'),
         models.Index(fields=['owner'], name='store_owner_ownerx'),
         models.Index(fields=['name'], name='store_name_namex')
   ]

   def __str__(self):
      return self.name
   

@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
   if created:
      Wallet.objects.get_or_create(store=instance)


class Product(models.Model):
   UPLOAD_STATUS = (
      ("Approved", "Approved"),
      ("Pending", "Pending"),
      ("Rejected", "Rejected")
   )

   id = models.CharField(max_length=36, default=uuid4, unique=True, primary_key=True)
   sku = models.CharField(max_length=8, unique=True, blank=True)
   name = models.CharField(max_length=50)
   description = models.TextField(null=True)
   quantity = models.IntegerField()
   category = models.ForeignKey('Category', related_name="category", on_delete=models.CASCADE, null=True)
   subcategory = models.ForeignKey('SubCategories', on_delete=models.CASCADE, null=True)
   producttype = models.ForeignKey('ProductTypes', on_delete=models.CASCADE, null=True)
   brand = models.ForeignKey('Brand', on_delete=models.CASCADE, null=True)
   created_at=models.DateTimeField(auto_now_add=True, null=True)
   on_promo = models.BooleanField(default=False)
   is_available = models.BooleanField(default=True)
   upload_status = models.CharField(max_length=8, choices=UPLOAD_STATUS, null=True, default="Pending")
   images = models.ManyToManyField('ProductImage')
   store = models.ManyToManyField('Store', related_name="store_products", blank=True)
   sales_count = models.IntegerField(default=0)


   class Meta:
      # Add an index for the 'uid' field
      indexes = [
         models.Index(fields=['id'], name='product_id_idx'),
         models.Index(fields=['sku'], name='product_sku_skux'),
         models.Index(fields=['name'], name='product_name_namex'),
         models.Index(fields=['category'], name= 'product_category_categoryx')
      ]
   
   def formatted_created_at(self):
      # Format the created_at field as "YMD, Timestamp"
      return self.created_at.strftime("%Y-%m-%d, %H:%M%p")
   
   def save(self, *args, **kwargs):
      # if not self.serial_number:
      #    self.serial_number = generate_unique_code()
      if not self.sku:
         self.sku = self._generate_sku()
      return super().save(*args, **kwargs)
   
   def _generate_sku(self):
      return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
      
   def __str__(self):
      return self.name


class ProductImage(models.Model):
   images = models.FileField(storage=RawMediaCloudinaryStorage)
   
   class Meta:
      indexes = [
      models.Index(fields=['images'], name='product_images_imagesx')
      ]


class ProductVariant(models.Model):
   COLOR_CHOICES = [
   ('Red', 'Red'),
   ('Orange', 'Orange'),
   ('Yellow', 'Yellow'),
   ('Green', 'Green'),
   ('Blue', 'Blue'),
   ('Purple', 'Purple'),
   ('Pink', 'Pink'),
   ('Brown', 'Brown'),
   ('Gray', 'Gray'),
   ('Black', 'Black'),
   ('White', 'White'),
   ('Cyan', 'Cyan'),
   ('Magenta', 'Magenta'),
   ('Lime', 'Lime'),
   ('Teal', 'Teal'),
   ('Indigo', 'Indigo'),
   ('Maroon', 'Maroon'),
   ('Olive', 'Olive'),
   ('Navy', 'Navy'),
   ('Silver', 'Silver'),
   ]
   
   product = models.ManyToManyField('Product', related_name='product_variants')
   size = models.CharField(max_length=50, null=True)
   colors = ArrayField(models.CharField(max_length=20, choices=COLOR_CHOICES))
   wholesale_price = models.DecimalField(max_digits=11, decimal_places=2)

   def __str__(self):
      return self.size


class StoreProductPricing(models.Model):
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='varied_products', null=True)
   store = models.ForeignKey('Store', on_delete=models.CASCADE)
   retail_price = models.DecimalField(max_digits=11, decimal_places=2)

   def __str__(self):
      return f"{self.store} - ${self.retail_price}"
   

@receiver(post_save, sender=StoreProductPricing)
def create_marketplace(sender, instance, created, **kwargs):
   if created:
      related_product = instance.product
      related_store = instance.store
      MarketPlace.objects.get_or_create(store=related_store, product=related_product)



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


class Cart(models.Model):
   user = models.ForeignKey(CustomUser, limit_choices_to={"is_consumer":True}, on_delete=models.CASCADE)
   store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
   product = models.ForeignKey(Product, on_delete=models.CASCADE)
   quantity = models.PositiveIntegerField(default=1)


class Wishlist(models.Model):
   user = models.ForeignKey(CustomUser, limit_choices_to={"is_consumer":True}, on_delete=models.CASCADE)
   product = models.ForeignKey(Product, on_delete=models.CASCADE)


class MarketPlace(models.Model):
   store=models.ForeignKey(Store, on_delete=models.CASCADE, db_index=True)
   product = models.ForeignKey(Product, related_name="products",on_delete=models.CASCADE, null=True, db_index=True)
   list_product = models.BooleanField(default=True, db_index=True)
   
   def __repr__(self):
      return f"MarketPlace(store={self.store.name}, product={self.product}, list_product={self.list_product})"


class ReportUser(models.Model):
   OFFENSE = (
      ('Inappropriate Behavior', 'Inappropriate Behavior'),
      ('Violating Terms of Service', 'Violating Terms of Service'),
      ('Shipping and Fulfillment Issues', 'Shipping and Fulfillment Issues'),
      ('Poor Customer Service', 'Poor Customer Service'),
      ('Unfair Competition Practices', 'Unfair Competition Practices'),
      ('Fraudulent Activities', 'Fraudulent Activities'),
      ('Others', 'Others')
   )
   
   STATUS = (
      ('Pending', 'Pending'),
      ('In-Progress', 'In-Progress'),
      ('Resolved', 'Resolved')
   )
   user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reported_user')
   title = models.CharField(max_length=31, choices=OFFENSE, null=True)
   other = models.CharField(max_length=30, null=True)
   details = models.TextField()
   support_code = models.CharField(max_length=10, default='')
   status = models.CharField(choices=STATUS, max_length=11, default='Pending')

   def __str__(self):
      return f"{self.user.first_name} {self.title}"
   
   def save(self, *args, **kwargs):
      if not self.support_code:
         self.support_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
      return super().save(*args, **kwargs)