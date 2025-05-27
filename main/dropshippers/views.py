from django.shortcuts import render
from mall.models import CustomUser, Store, Product, Category
from mall.serializers import ProductSerializer
from rest_framework.generics import RetrieveAPIView, ListAPIView
from django.shortcuts import get_object_or_404, get_list_or_404

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import DropshipperAdminSerializer
from cloudinary import uploader

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
   
class DropshipperAdminViewSet(viewsets.ModelViewSet):
   """
   Admin-only dropshipper management
   """
   queryset = CustomUser.objects.filter(is_store_owner=True)
   serializer_class = DropshipperAdminSerializer
   permission_classes = [IsAdminUser]
   lookup_field = 'id'

   def update(self, request, *args, **kwargs):
      """
      Handle full update - signals will manage Cloudinary deletion
      """
      return super().update(request, *args, **kwargs)

   def partial_update(self, request, *args, **kwargs):
      """
      Handle partial update - signals will manage Cloudinary deletion
      """
      return super().partial_update(request, *args, **kwargs)

   def destroy(self, request, *args, **kwargs):
      instance = self.get_object()

      # Delete profile image first
      if instance.profile_image:
         try:
            instance.profile_image.delete()
         except Exception as e:
            print(f"Cloudinary deletion error: {str(e)}")
      
      # Delete related store and products
      if hasattr(instance, 'owners'):
         instance.owners.delete()  # Cascade delete store and related objects
         
      self.perform_destroy(instance)
      return Response(status=status.HTTP_204_NO_CONTENT)

   def perform_create(self, serializer):
      serializer.save(is_store_owner=True)  # Force store owner status

   def get_queryset(self):
      return super().get_queryset().select_related(
         'owners'
      ).prefetch_related(
         'owners__store_orders',
         'owners__pricings'
      )