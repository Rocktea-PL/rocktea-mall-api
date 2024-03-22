from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from mall.models import CustomUser, Store, Product, Category, SubCategories, StoreProductPricing, Product, ProductVariant

from django.shortcuts import get_object_or_404
from rest_framework.parsers import JSONParser
from workshop.processor import DomainNameHandler

handler = DomainNameHandler()

def get_store_domain(request):
   return request.META.get("HTTP_ORIGIN")

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


class GetVariantAndPricing(APIView):
   parser_classes = [JSONParser]

   def get(self, request, **kwargs):
      product_id = kwargs.get('product_id')
      
      try:
         # Attempt to get the store_id using the domain name
         store_id = handler.process_request(domain_name=get_store_domain(request))
      except Exception as e:
         # If an error occurs, fallback to getting the store_id from query parameters
         store_id = request.query_params.get("store")
         if not store_id:
               raise Http404("Store not found")  # or return a more suitable error response

      verified_product = get_object_or_404(Product, id=product_id)
      verified_store = get_object_or_404(Store, id=store_id)

      variants = ProductVariant.objects.filter(product=verified_product)

      data = {
         "product": verified_product.name,
         "variants": [
               {
                  "id": variant.id,
                  "size": variant.size,
                  "colors": variant.colors,
                  "wholesale_price": variant.wholesale_price,
                  "store_pricings": {
                     "retail_price": self.get_store_pricing(verified_product.id, verified_store)
                  },
               }
               for variant in variants
         ],
      }
      return Response(data)

   def get_store_pricing(self, product, store):
      try:
         store_product = StoreProductPricing.objects.get(
               product=product, store=store)
      except StoreProductPricing.DoesNotExist:
         return None  # Handle the case when pricing information is not available

      return store_product.retail_price