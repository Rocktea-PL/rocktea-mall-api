from django.shortcuts import render
from .serializers import ServicesSerializer, ServicesLogin
from mall.models import CustomUser
from rest_framework import viewsets, permissions
from rest_framework_simplejwt.views import TokenObtainPairView


# Create your views here.
class SignUpServices(viewsets.ModelViewSet):
   queryset = CustomUser.objects.filter(is_services=True)
   serializer_class = ServicesSerializer


class SignInServicesView(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = ServicesLogin