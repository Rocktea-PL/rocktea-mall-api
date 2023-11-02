from django.http import Http404
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItems, Store, CustomUser
from mall.models import Product
from .serializers import OrderSerializer, OrderItemsSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
import logging
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist


class OrderItemsViewSet(ModelViewSet):
   queryset = OrderItems.objects.all()
   serializer_class = OrderItemsSerializer

class OrderViewSet(ModelViewSet):
   queryset = Order.objects.all()
   serializer_class = OrderSerializer
