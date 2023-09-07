from .models import CustomUser
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ReadOnlyField
from .models import CustomUser, Store, Category, SubCategories

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