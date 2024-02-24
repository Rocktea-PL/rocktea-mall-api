from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions, viewsets
from .serializers import UserLogin, StoreUserSignUpSerializer
from mall.models import CustomUser
from rest_framework.renderers import JSONRenderer
from workshop.exceptions import ValidationError
from workshop.processor import DomainNameHandler
from django.shortcuts import get_object_or_404

# Create your views here.

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