from .models import CustomUser
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ReadOnlyField
from .models import CustomUser, Store, Category, SubCategories
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class StoreOwnerSerializer(ModelSerializer):
   class Meta:
      model=CustomUser
      fields = ("uid", "first_name", "last_name", "username", "email", "contact", "profile_image", "is_store_owner","password")
      
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
      

class SignInUser(TokenObtainPairSerializer):
   username_field = 'email'
   
   @classmethod
   def get_token(cls, user):
        token = super().get_token(user)
        return token

   def validate(self, attrs):
      data = super().validate(attrs)
      user = self.user
      
      # Get user data
      data['user_data'] = {
         "uid": user.uid,
         "first_name": user.first_name,
         "last_name": user.last_name,
         "email": user.email,
         "username": getattr(user, 'username', None),
         "profile_image": getattr(user.profile_image, 'url', None),
         "is_store_owner": user.is_store_owner,
         "is_consumer": user.is_consumer
      }
      refresh = self.get_token(user)
      data["refresh"] = str(refresh)
      data["access"] = str(refresh.access_token)
      return data