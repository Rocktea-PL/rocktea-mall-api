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
            username = self.generate_unique_username()
        if not email:
            raise ValueError('The Email field must be set')

        # Check password validity
        if password:
            self.validate_password(password)

        user = self.model(
            username=username,
            email=email,
            is_store_owner=is_store_owner,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def generate_unique_username(self):
        while True:
            username = generate_unique_code()
            if not self.model.objects.filter(username=username).exists():
                return username

    def validate_password(self, password):
        """
        Custom password validation logic to ensure it contains
        symbols, digits, uppercase, and lowercase characters.
        """
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one digit.')
        if not any(char.isupper() for char in password):
            raise ValueError(
                'Password must contain at least one uppercase character.')
        if not any(char.islower() for char in password):
            raise ValueError(
                'Password must contain at least one lowercase character.')
        if not any(not char.isalnum() for char in password):
            raise ValueError('Password must contain at least one symbol.')


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
   year_of_establishment = models.DateField(validators=[YearValidator])
   domain_name = models.CharField(max_length=100, unique=True)
   store_url = models.URLField(unique=True)

   def __str__(self):
      return self.name


class Product(models.Model):
   COLORS = (
      # Existing colors
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

      # Additional colors (not already in the list)
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
   category = models.ForeignKey('Category', on_delete=models.CASCADE)
   
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
   category = models.ForeignKey(Category, related_name="categories", on_delete=models.CharField)
   name = models.CharField(max_length=30)
   
   def __str__(self):
      return self.name


class Brand(models.Model):
   category = models.OneToOneField(Category, on_delete=models.CASCADE)
   name = models.CharField(max_length=25, unique=True)
   
   # i stopped at Health and Beauty