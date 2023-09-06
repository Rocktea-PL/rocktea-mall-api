from .models import CustomUser
from rest_framework.serializers import ModelSerializer
from .models import CustomUser, Store

class StoreOwnerSerializer(ModelSerializer):
   class Meta:
      model=CustomUser
      fields = ("uid", "first_name", "last_name", "email", "contact", "profile_image", "is_store_owner","password")
      
   def create(self, validated_data):
      # extract password from validated_data list
      password = validated_data.pop("password", None)

      user = CustomUser.objects.create(**validated_data)
      # confirm user as store_owner
      user.is_store_owner=True
      if password:
         user.set_password(password)
         user.save()
         
      return user