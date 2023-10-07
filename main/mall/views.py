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
      
   # def put(self, request, *args, **kwargs):
   #    instance = self.get_object()
   #    serializer = self.get_serializer(instance, data=request.data, partial=True)
   #    serializer.is_valid(raise_exception=True)

   #    # Check if 'category' is present in the request data and extract the ID
   #    category_data = request.data.get('category', {})
   #    category_id = category_data.get('id')

   #    # Update the request data to only include the ID for the 'category' field
   #    request.data['category'] = category_id

   #    self.perform_update(serializer)

   #    return Response(serializer.data)
      
   
# Sign In Users
# class SignInUserView(TokenObtainPairView):
#    permission_classes = (permissions.AllowAny,)
#    serializer_class = MyTokenObtainPairSerializer

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