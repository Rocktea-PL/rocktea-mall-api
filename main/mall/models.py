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
    def create_user(self, username, email, password=None, is_store_owner=False):
        if not username:
            username = self.generate_username()

        if CustomUser.objects.filter(username=username).exists():
            raise ValueError('Username is already in use.')

        if CustomUser.objects.filter(email=email).exists():
            raise ValueError('Email is already in use.')

        if not email:
            raise ValueError('The Email field must be set')

        # Check password validity
        if password:
            # Validate the password using regular expressions
            if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).+$', password):
                raise ValueError('Password does not meet the requirements.')

        user = self.model(
            username=username,
            email=email,
            is_store_owner=is_store_owner,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def generate_username():
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
            if not CustomUser.objects.filter(username=code).exists():
                return code


# StoreOwner models
class CustomUser(AbstractBaseUser):
    uid = models.UUIDField(default=uuid4, unique=True,
                           primary_key=True, db_index=True)
    username = models.CharField(max_length=5, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    contact = PhoneNumberField()
    is_store_owner = models.BooleanField(default=False)
    is_consumer = models.BooleanField(default=False)
    password = models.CharField(max_length=200)
    associated_domain = models.ForeignKey("Store", on_delete=models.CASCADE, null=True)
    profile_image = models.FileField(storage=RawMediaCloudinaryStorage)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        # Add an index for the 'uid' field
        indexes = [
            models.Index(fields=['uid'], name='uid_idx'),
        ]

    def __str__(self):
        return self.first_name


class Store(models.Model):
   owner = models.OneToOneField(CustomUser, related_name="owners",
                                on_delete=models.CASCADE, limit_choices_to={"is_store_owner": True})
   name = models.CharField(max_length=150, unique=True)
   email = models.EmailField(unique=True)
   TIN_number = models.IntegerField()
   logo = models.FileField(storage=RawMediaCloudinaryStorage)
   cover_image = models.FileField(storage=RawMediaCloudinaryStorage, null=True)
   year_of_establishment = models.DateField(validators=[YearValidator])
   domain_name = models.CharField(max_length=100, unique=True)
   category = models.OneToOneField('Category', on_delete=models.CASCADE, null=True)
   store_url = models.URLField(unique=True)

   def __str__(self):
      return self.name


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

   sn = models.IntegerField(unique=True)
   sku = models.CharField(max_length=8, unique=True)
   name = models.CharField(max_length=50)
   quantity = models.IntegerField()
   color = models.CharField(choices=COLORS, max_length=9)
   category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True)
   subcategory = models.ForeignKey('SubCategories', on_delete=models.CASCADE, null=True)
   brand = models.ForeignKey('Brand', on_delete=models.CASCADE, null=True)
   is_available = models.BooleanField(default=True)
   created_at=models.DateTimeField(auto_created=True, null=True)
   on_promo = models.BooleanField(default=False)
   
   
   def formatted_created_at(self):
        # Format the created_at field as "YMD, Timestamp"
        return self.created_at.strftime("%Y-%m-%d, %H:%M:%S")
    
   def save(self, *args, **kwargs):
      if not self.sn:
         self.sn = generate_unique_code()
      if not self.sku:
         self.sku = self._generate_sku()
      return super().save(*args, **kwargs)
   
   def _generate_sku(self):
      return "".join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=8))
      
   def __str__(self):
      return self.sn


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
   
   def __str__(self):
      return self.name


class SubCategories(models.Model):
   category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CharField)
   name = models.CharField(max_length=30)
   
   def __str__(self):
      return self.name


class Brand(models.Model):
   subcategory = models.ManyToManyField(SubCategories)
   name = models.CharField(max_length=25, unique=True)
   
   def __str__(self):
       return self.name