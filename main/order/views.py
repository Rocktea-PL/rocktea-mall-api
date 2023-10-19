from django.shortcuts import render, get_object_or_404
from .models import Order, OrderItems
from .serializers import OrderSerializer
from rest_framework.generics import ListCreateAPIView, GenericAPIView
from rest_framework.views import APIView

# from .serializers import Or

# Create your views here.
class CreateOrder(APIView):
   def post(self, request, *args):
      
      # Make request.data reusable
      collect = request.data
      buyer_id = request.user.id
      
      # collect store & buyer id
      store_id = self.get_store(collect['store'])   
      buyer_id = self.get_buyer(buyer_id)
      
      order = Order.objects.create(buyer=buyer_id, store=store_id)
   
      
   def get_store(self, store):
      verified_store = get_object_or_404(Store, id=store)
      return verified_store

   def get_buyer(self, buyer):
      verified_user = get_object_or_404(CustomUser, id=buyer)
      return verified_user
      
      
      