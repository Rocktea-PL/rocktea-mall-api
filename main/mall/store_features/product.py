from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mall.models import CustomUser, Store, Product, Category, SubCategories



class MyProducts(APIView):
   """
   This API is to get specific products for StoreOwners based on the Category of Products they chose
   to deal, on registration
   """

   def get_store_owner(self, owner_uid):
      try:
         owner = CustomUser.objects.filter(is_store_owner=True, uid=owner_uid).first()
      except CustomUser.DoesNotExist:
         raise ValueError("Sorry you need to Sign Up or Login first")
      return owner