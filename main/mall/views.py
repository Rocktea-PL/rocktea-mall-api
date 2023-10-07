from rest_framework import viewsets
from .serializers import StoreOwnerSerializer, SubCategorySerializer, CategorySerializer, MyTokenObtainPairSerializer, CreateStoreSerializer
from .models import CustomUser, Category, Store, Product
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import serializers
from helpers.views import BaseView
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.
class CreateStoreOwner(viewsets.ModelViewSet):
   """
   Sign Up Store Owners Feature
   """
   queryset = CustomUser.objects.all()
   serializer_class = StoreOwnerSerializer
   renderer_classes= [JSONRenderer]


class CreateStore(viewsets.ModelViewSet):
   """
   Create Store Feature 
   """
   queryset = Store.objects.all()
   serializer_class = CreateStoreSerializer

   def perform_create(self, serializer):
      # Assign the current user to the 'owner' field
      serializer.save(owner=self.request.user)
      
   def perform_update(self, serializer):
      # You can override this method to add custom logic when updating the instance
      serializer.save()

# Sign In Store User
class SignInUserView(BaseView):
   required_post_fields = ["email", "password"]
   def post(self, request, format=None):
      res = super().post(request, format)
      if res:
         return res
      
      try:
         user = CustomUser.objects.get(is_store_owner=True, email=request.data["email"])
      except CustomUser.DoesNotExist:
         raise serializers.ValidationError({"error": "User does not exist"})

      if user.check_password(raw_password=request.data["password"]):
         token = RefreshToken.for_user(user)
         print(token)
         res = {
               "code":200,
               "message":"success",
               # "user": jsonify_user(user),
               "token":str(token.access_token),
         }
         return Response(res, 200)
      else:
         res = {
               "code":400,
               "message":"invalid credentials"
         }
         return Response(res, 400)


class GetCategories(viewsets.ReadOnlyModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer #TODO Differ this based on user