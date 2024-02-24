from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions, viewsets
from .serializers import UserLogin, StoreUserSignUp
from mall.models import CustomUser
from rest_framework.renderers import JSONRenderer
from workshop.exceptions import ValidationError

# Create your views here.

class TenantSignUp(viewsets.ModelViewSet):
   serializer_class = StoreUserSignUp
   renderer_classes = [JSONRenderer]

   def get_queryset(self):
      user = self.request.query_params.get("mallcli")
      try:
         queryset = CustomUser.objects.filter(id=user, is_consumer=True)
      except CustomUser.DoesNotExist:
         raise ValidationError("User Does Not Exist")

      return queryset


class LoginStoreUser(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = UserLogin