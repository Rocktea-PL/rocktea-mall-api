from django.shortcuts import render
from mall.models import CustomUser, Store, Product, Category
from mall.serializers import ProductSerializer
from rest_framework.generics import RetrieveAPIView, ListAPIView
from django.shortcuts import get_object_or_404, get_list_or_404

# Create your views here.
# Get Store Products by Category
class MyProducts(ListAPIView):
   serializer_class = ProductSerializer

   def get_queryset(self, *args, **kwargs):
      category = self.request.query_params.get("category")
      
      # Verify category using get_list_or_404
      verified_category = get_list_or_404(Category, id=category)
      
      # Filter Product By Catgery
      queryset = Product.objects.filter(category__in=verified_category)
      return queryset