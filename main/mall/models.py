from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from uuid import uuid4
import random, string
from phonenumber_field.modelfields import PhoneNumberField
from cloudinary_storage.storage import RawMediaCloudinaryStorage


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
            raise ValueError('Password must contain at least one uppercase character.')
        if not any(char.islower() for char in password):
            raise ValueError('Password must contain at least one lowercase character.')
        if not any(not char.isalnum() for char in password):
            raise ValueError('Password must contain at least one symbol.')


# StoreOwner models
class CustomUser(AbstractBaseUser):
   uid = models.UUIDField(default=uuid4, unique=True, primary_key=True, db_index=True)
   username = models.CharField(max_length=5, unique=True)
   email = models.EmailField(unique=True)
   first_name = models.CharField(max_length=250)
   last_name = models.CharField(max_length=250)
   contact = PhoneNumberField()
   is_store_owner = models.BooleanField(default=False)
   password = models.CharField(max_length=200)
   profile_image = models.FileField(storage=RawMediaCloudinaryStorage)
   
   objects = CustomUserManager()
   
   USERNAME_FIELD='email'
   REQUIRED_FIELDS = []
   
   class Meta:
        # Add an index for the 'uid' field
      indexes = [
            models.Index(fields=['uid'], name='uid_idx'),
        ]
   
   def __str__(self):
       return self.first_name