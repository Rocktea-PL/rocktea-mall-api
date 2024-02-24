from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions, viewsets
from .serializers import UserLogin, StoreUserSignUpSerializer
from mall.models import CustomUser
from rest_framework.renderers import JSONRenderer
from workshop.exceptions import ValidationError

# Create your views here.

class TenantSignUp(viewsets.ModelViewSet):
   serializer_class = StoreUserSignUpSerializer
   renderer_classes = [JSONRenderer]

   def get_queryset(self):
      user = self.request.query_params.get("mallcli")
      # print(user)
      try:
         queryset = CustomUser.objects.filter(id=user, is_consumer=True)
         print(queryset)
      except CustomUser.DoesNotExist:
         raise ValidationError("User Does Not Exist")
      
      if not queryset.exists():
         raise ValidationError("User is Not a Store User")
      
      return queryset

class LoginStoreUser(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = UserLogin