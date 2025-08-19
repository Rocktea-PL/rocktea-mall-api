from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions, viewsets, status
from rest_framework.views import APIView
from .serializers import UserLogin, StoreUserSignUpSerializer
from mall.models import CustomUser
from rest_framework.renderers import JSONRenderer
from workshop.exceptions import ValidationError
from workshop.processor import DomainNameHandler
# Create your views here.

from rest_framework.response import Response
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from setup.image_utils import ImageOptimizer
import base64

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

# Configure the logger
logger = logging.getLogger(__name__)

handler = DomainNameHandler()

class TenantSignUp(viewsets.ModelViewSet):
   serializer_class = StoreUserSignUpSerializer
   renderer_classes = [JSONRenderer]

   def get_queryset(self):
      user_id = self.request.query_params.get("mallcli")

      try:
         queryset = CustomUser.objects.filter(id=user_id, is_consumer=True)
         # print(queryset)
      except CustomUser.DoesNotExist:
         raise ValidationError("User Does Not Exist")
      
      if not queryset.exists():
         raise ValidationError("User is Not a Store User")
      
      return queryset


class LoginStoreUser(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = UserLogin

class VerifyEmail(APIView):
   permission_classes = (permissions.AllowAny,)
   
   @swagger_auto_schema(
      manual_parameters=[
         openapi.Parameter(
            'token',
            openapi.IN_QUERY,
            description="Verify email upon registration",
            type=openapi.TYPE_STRING,
            required=True
         )
      ],
      responses={
         200: openapi.Response(
               description="Email verified successfully",
               examples={
                  "application/json": {
                     "message": "Email successfully verified"
                  }
               }
         ),
         400: openapi.Response(
               description="Bad request",
               examples={
                  "application/json": {
                     "error": "Token is required"
                  }
               }
         ),
         404: openapi.Response(  # Added 404 response
               description="Not found",
               examples={
                  "application/json": {
                     "error": "Invalid token"
                  }
               }
         )
      }
   )
   def get(self, request):
      """
      Verify user's email using the provided token
      
      This endpoint validates the email verification token sent to the user's email.
      Upon successful verification, the user's account is activated.
      """
      token = request.query_params.get('token')
      if not token:
         return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
      
      try:
         # Get user by verification_token (should be indexed in model)
         user = CustomUser.objects.get(verification_token=token)
         
         # Create token generator instance
         token_generator = PasswordResetTokenGenerator()
         
         if token_generator.check_token(user, token):
            # Only update if not already verified
            if not user.is_verified:
               user.is_verified = True
               user.is_active = True
               user.verification_token = None  # Invalidate after use
               user.verification_token_created_at = None
               user.save()
               return Response({'message': 'Email successfully verified'}, status=status.HTTP_200_OK)
            else:
               return Response({'message': 'Email is already verified'}, status=status.HTTP_200_OK)
         else:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
               
      except CustomUser.DoesNotExist:
         return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)
      except Exception as e:
         logger.error(f"Email verification error: {str(e)}")
         return Response({'error': 'An error occurred during verification'}, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfile(APIView):
   permission_classes = [permissions.IsAuthenticated]
   parser_classes = [MultiPartParser, FormParser]
   
   @swagger_auto_schema(
      request_body=openapi.Schema(
         type=openapi.TYPE_OBJECT,
         properties={
            'profile_image': openapi.Schema(type=openapi.TYPE_FILE),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            'contact': openapi.Schema(type=openapi.TYPE_STRING),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
         }
      ),
      responses={
         200: openapi.Response(description="Profile updated successfully"),
         400: openapi.Response(description="Validation error")
      }
   )
   def patch(self, request):
      """Update user profile with background image processing"""
      try:
         user = request.user
         data = request.data
         
         # Fields that can be updated
         updatable_fields = ['first_name', 'last_name', 'contact', 'username']
         updated_fields = []
         
         # Update text fields
         for field in updatable_fields:
            if field in data and data[field]:
               setattr(user, field, data[field])
               updated_fields.append(field)
         
         # Handle profile image with optimization
         if 'profile_image' in request.FILES:
            image_file = request.FILES['profile_image']
            
            try:
               # Delete old profile image if exists
               if user.profile_image:
                  try:
                     user.profile_image.delete(save=False)
                  except Exception as e:
                     logger.warning(f"Profile image deletion error: {e}")
               
               # Save the uploaded file directly - Cloudinary storage will handle optimization
               user.profile_image = image_file
               updated_fields.append('profile_image')
            except Exception as e:
               logger.error(f"Image upload error: {str(e)}")
               return Response({'error': 'Image upload failed'}, status=status.HTTP_400_BAD_REQUEST)
         
         # Save user with updated fields
         if updated_fields:
            user.save(update_fields=updated_fields)
            
            response_data = {'message': 'Profile updated successfully'}
            if 'profile_image' in updated_fields:
               response_data['profile_image_url'] = user.profile_image.url if user.profile_image else None
            
            return Response(response_data, status=status.HTTP_200_OK)
         
         return Response({'message': 'No fields to update'}, status=status.HTTP_400_BAD_REQUEST)
      
      except Exception as e:
         logger.error(f"Profile update error: {str(e)}")
         return Response({'error': 'Profile update failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)