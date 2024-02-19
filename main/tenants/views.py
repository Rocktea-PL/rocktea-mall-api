from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions, viewsets
from .serializers import UserLogin, StoreUserSignUp
from mall.models import CustomUser
from rest_framework.renderers import JSONRenderer

# Create your views here.


class TenantSignUp(viewsets.ModelViewSet):
   queryset = CustomUser.objects.filter(is_consumer=True)
   serializer_class = StoreUserSignUp
   renderer_classes = [JSONRenderer]



class LoginStoreUser(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = UserLogin