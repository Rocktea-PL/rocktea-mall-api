from mall.models import CustomUser, StoreDomainPaymentInfo
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from django.conf import settings
import requests
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from django.http import QueryDict
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

class StoreOTPPayment(APIView):
   @csrf_exempt
   @transaction.atomic
   def post(self, request: HttpRequest):
      user_id = request.POST.get("store_owner")
      
      # VERIFY USER EXISTENCE
      user_exists = get_user_model().objects.filter(id=user_id, is_store_owner=True, is_consumer=False).first()
      if user_exists:
         # Process your payment logic here
         payment_response = self.process_payment(request)
         return payment_response
      else:
         return Response({"message": "Invalid store owner user ID."}, status=status.HTTP_400_BAD_REQUEST)

   @transaction.atomic
   def process_payment(self, request: HttpRequest):
      url = "https://api.paystack.co/transaction/initialize"
      headers = {
         'Content-Type': 'application/json',
         'Authorization': f'Bearer {settings.TEST_SECRET_KEY}'
      }
      print(settings.TEST_SECRET_KEY)
      # Get User Data
      user = self.collect_user(request)

      payload = {
         "email": user.email,
         "amount": 50000,
      }

      response = requests.post(url, headers=headers, json=payload)
      if response.status_code == 200:
         data = response.json()
         return Response(data, status=status.HTTP_200_OK)
      else:
         return Response({"message": f"{response.text}"}, status=status.HTTP_400_BAD_REQUEST)

   def collect_user(self, request: HttpRequest):
      user_id = request.data.get("store_owner")
      
      # VERIFY USER EXISTENCE
      user_exists = get_user_model().objects.filter(id=user_id, is_store_owner=True, is_consumer=False).first()
      try:
         # VERIFY USER EXISTENCE
         user_exists = get_user_model().objects.filter(id=user_id, is_store_owner=True, is_consumer=False).first()
         if user_exists:
               return user_exists
         else:
               raise ValueError("Invalid store owner user ID.")
      except IntegrityError as e:
         raise ValueError(f"Database error: {e}")
      



# ...
class VerifyPayment(APIView):
   def get(self, request):
      # Use QueryDict to get query parameters
      reference = self.request.query_params.get("reference")

      headers = {
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {settings.TEST_SECRET_KEY}'
      }

      url = f"https://api.paystack.co/transaction/verify/{reference}"

      response = requests.get(url, headers=headers)

      if response.status_code == 200:
         response_data = response.json()
         return Response(response_data, status=status.HTTP_200_OK)
      else:
         response_data = response.text
         return Response({"message": f'{response_data}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
   # def collect_user(self, request):
      
   #    store_owner = request.data.get('id')
   #    store_owner_exists = CustomUser.objects.filter(id=store_owner, is_store_owner=True, is_consumer=False).first()
   #    # if store_owner_exists:
   #    #    print(store_owner_exists)
   #    # else:
   #    #    print("Doesn't Exist")
