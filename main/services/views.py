from django.shortcuts import render
from .serializers import ServicesSerializer, ServicesLogin, ServicesCategorySerializer
from mall.models import CustomUser
from rest_framework import viewsets, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import ServicesCategory

# Create your views here.
class SignUpServices(viewsets.ModelViewSet):
   queryset = CustomUser.objects.filter(is_services=True)
   serializer_class = ServicesSerializer


class SignInServicesView(TokenObtainPairView):
   permission_classes = (permissions.AllowAny,)
   serializer_class = ServicesLogin


class ServicesCategoryView(viewsets.ModelViewSet):
   queryset = ServicesCategory.objects.all()
   serializer_class = ServicesCategorySerializer