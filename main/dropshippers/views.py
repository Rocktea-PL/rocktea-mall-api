from mall.models import CustomUser, Product, Category
from mall.serializers import ProductSerializer
from rest_framework.generics import ListAPIView
from django.shortcuts import get_list_or_404

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import DropshipperAdminSerializer, DropshipperListSerializer, DropshipperDetailSerializer

from django.db.models import Count, Sum, Q, Case, When, BooleanField, DecimalField, IntegerField, Prefetch
from django.db.models.functions import Coalesce
from mall.models import Product
from order.models import StoreOrder
from mall.models import StoreProductPricing

from django.utils import timezone
from order.pagination import CustomPagination

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .filters import DropshipperFilter
from django.core.cache import cache

# Create your views here.
# Get Store Products by Category
class MyProducts(ListAPIView):
   serializer_class = ProductSerializer

   def get_queryset(self, *args, **kwargs):
      category = self.request.query_params.get("category")
      
      if not category:
         return Product.objects.none()
      
      try:
         verified_category = get_list_or_404(Category, id=category)
         return Product.objects.filter(category__in=verified_category).select_related('category')
      except:
         return Product.objects.none()

class DropshipperAdminViewSet(viewsets.ModelViewSet):
   """Optimized admin-only dropshipper management with analytics"""
   permission_classes = [IsAdminUser]
   lookup_field = 'id'
   pagination_class = CustomPagination

   filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
   filterset_class = DropshipperFilter
   search_fields = ['email', 'first_name', 'last_name', 'owners__name']
   ordering_fields = ['date_joined', 'last_login', 'total_revenue']
   ordering = ['-date_joined']

   def get_serializer_class(self):
      if self.action == 'list':
         return DropshipperListSerializer
      elif self.action in ['create', 'update', 'partial_update']:
         return DropshipperAdminSerializer
      return DropshipperDetailSerializer

   def destroy(self, request, *args, **kwargs):
      try:
         instance = self.get_object()

         # Safe image deletion with Cloudinary
         if hasattr(instance, 'profile_image') and instance.profile_image:
            try:
               # Extract public_id from Cloudinary URL
               image_url = str(instance.profile_image)
               if 'cloudinary.com' in image_url:
                  import cloudinary.uploader as uploader
                  # Extract public_id from URL (format: .../upload/v123456/folder/filename.ext)
                  parts = image_url.split('/')
                  if 'upload' in parts:
                     upload_index = parts.index('upload')
                     if upload_index + 2 < len(parts):
                        # Skip version if present (v123456)
                        start_index = upload_index + 2 if parts[upload_index + 1].startswith('v') else upload_index + 1
                        public_id_parts = parts[start_index:]
                        public_id = '/'.join(public_id_parts).split('.')[0]  # Remove extension
                        uploader.destroy(public_id)
               # Delete the file field
               instance.profile_image.delete(save=False)
            except Exception as e:
               print(f"Image deletion error: {str(e)}")
         
         # Delete related store (cascade handles the rest)
         if hasattr(instance, 'owners') and instance.owners:
            instance.owners.delete()
            
         self.perform_destroy(instance)
         return Response(status=status.HTTP_204_NO_CONTENT)
      except Exception as e:
         return Response({
            'error': 'Failed to delete dropshipper',
            'details': str(e)
         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def create(self, request, *args, **kwargs):
      try:
         serializer = self.get_serializer(data=request.data)
         if not serializer.is_valid():
            # Handle validation errors with user-friendly messages
            for field, field_errors in serializer.errors.items():
               if field == 'email' and any('already exists' in str(error).lower() for error in field_errors):
                  return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'contact' and any('already exists' in str(error).lower() for error in field_errors):
                  return Response({'error': 'A user with this contact number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'username' and any('already exists' in str(error).lower() for error in field_errors):
                  return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'company_name':
                  return Response({'error': 'A store with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'TIN_number':
                  return Response({'error': 'A store with this TIN number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            # Return first error if no specific match
            first_error = next(iter(serializer.errors.values()))[0]
            return Response({'error': str(first_error)}, status=status.HTTP_400_BAD_REQUEST)
         
         self.perform_create(serializer)
         
         # Get the created user with store data
         user = serializer.instance
         store_data = None
         if hasattr(user, 'owners') and user.owners:
            store = user.owners
            store_data = {
               'id': store.id,
               'name': store.name,
               'email': user.email,
               'domain_name': store.domain_name,
               'logo': store.logo.url if store.logo else None,
               'cover_image': store.cover_image.url if store.cover_image else None,
               'category': {
                  'id': store.category.id,
                  'name': store.category.name
               } if store.category else None
            }
         
         return Response({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'email': user.email,
            'contact': str(user.contact) if user.contact else None,
            'profile_image': self._get_optimized_profile_image(user.profile_image),
            'is_store_owner': user.is_store_owner,
            'completed_steps': user.completed_steps,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'date_joined': user.date_joined,
            'last_active': user.last_login,
            'total_products': 0,
            'total_products_available': 0,
            'total_products_sold': 0,
            'total_revenue': 0,
            'store': store_data,
            'is_active_user': False,
            'company_name': store_data['name'] if store_data else None
         }, status=status.HTTP_201_CREATED)
      except Exception as e:
         # Handle any remaining errors
         error_msg = str(e)
         if 'email' in error_msg.lower() and 'already exists' in error_msg.lower():
            return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         elif 'contact' in error_msg.lower() and 'already exists' in error_msg.lower():
            return Response({'error': 'A user with this contact number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         elif 'username' in error_msg.lower() and 'already exists' in error_msg.lower():
            return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         else:
            return Response({'error': 'Failed to create dropshipper'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def update(self, request, *args, **kwargs):
      try:
         partial = kwargs.pop('partial', False)
         instance = self.get_object()
         
         serializer = self.get_serializer(instance, data=request.data, partial=partial)
         if not serializer.is_valid():
            # Handle validation errors with user-friendly messages
            for field, field_errors in serializer.errors.items():
               if field == 'company_name':
                  return Response({'error': 'A store with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'TIN_number':
                  return Response({'error': 'A store with this TIN number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'email':
                  return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'contact':
                  return Response({'error': 'A user with this contact number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
               elif field == 'username':
                  return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            # Return first error if no specific match
            first_error = next(iter(serializer.errors.values()))[0]
            return Response({'error': str(first_error)}, status=status.HTTP_400_BAD_REQUEST)
         
         self.perform_update(serializer)
         
         # Get updated user with store data
         user = instance
         store_data = None
         if hasattr(user, 'owners') and user.owners:
            store = user.owners
            store_data = {
               'id': store.id,
               'name': store.name,
               'email': user.email,
               'domain_name': store.domain_name,
               'logo': store.logo.url if store.logo else None,
               'cover_image': store.cover_image.url if store.cover_image else None,
               'category': {
                  'id': store.category.id,
                  'name': store.category.name
               } if store.category else None
            }
         
         return Response({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'email': user.email,
            'contact': str(user.contact) if user.contact else None,
            'profile_image': self._get_optimized_profile_image(user.profile_image),
            'is_store_owner': user.is_store_owner,
            'completed_steps': user.completed_steps,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'date_joined': user.date_joined,
            'last_active': user.last_login,
            'store': store_data,
            'is_active_user': False,
            'company_name': store_data['name'] if store_data else None
         })
      except Exception as e:
         error_msg = str(e)
         if 'store with this name already exists' in error_msg.lower():
            return Response({'error': 'A store with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         elif 'store with this tin number already exists' in error_msg.lower():
            return Response({'error': 'A store with this TIN number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         elif 'email already exists' in error_msg.lower():
            return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         elif 'contact already exists' in error_msg.lower():
            return Response({'error': 'A user with this contact number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         elif 'username already exists' in error_msg.lower():
            return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
         else:
            return Response({'error': 'Failed to update dropshipper'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
   def get_queryset(self):
      # Use only() to limit fields and reduce data transfer
      return CustomUser.objects.filter(
         is_store_owner=True
      ).select_related('owners__category').only(
         'id', 'first_name', 'last_name', 'email', 'username', 'contact',
         'profile_image', 'is_store_owner', 'completed_steps', 'is_active',
         'is_verified', 'date_joined', 'last_login',
         'owners__id', 'owners__name', 'owners__domain_name', 'owners__logo',
         'owners__cover_image', 'owners__category__id', 'owners__category__name'
      ).order_by('-date_joined')
   
   http_method_names = ['get', 'post', 'put', 'patch', 'delete']
   
   def _get_optimized_profile_image(self, profile_image):
      """Get optimized profile image URL using Cloudinary"""
      if not profile_image:
         return None
      
      try:
         from mall.cloudinary_utils import CloudinaryOptimizer
         # Extract public_id from Cloudinary URL
         image_url = str(profile_image)
         if 'cloudinary.com' in image_url:
            # Extract public_id from URL
            parts = image_url.split('/')
            if 'upload' in parts:
               upload_index = parts.index('upload')
               if upload_index + 2 < len(parts):
                  start_index = upload_index + 2 if parts[upload_index + 1].startswith('v') else upload_index + 1
                  public_id_parts = parts[start_index:]
                  public_id = '/'.join(public_id_parts).split('.')[0]
                  return CloudinaryOptimizer.get_optimized_url(public_id, 'thumbnail')
         # Fallback to original URL
         return image_url if hasattr(profile_image, 'url') else str(profile_image)
      except Exception:
         # Fallback to regular URL
         return profile_image.url if hasattr(profile_image, 'url') else str(profile_image)