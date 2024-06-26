from mall.models import CustomUser
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
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

def get_user_or_none(user_id):
   try:
      user = get_user_model().objects.get(Q(id=user_id, is_store_owner=True) | Q(id=user_id, is_services=True), is_consumer=False)
      return user
   except ObjectDoesNotExist:
      return None
   except IntegrityError as e:
      raise ValueError(f"Database error: {e}")


class StoreOTPPayment(APIView):
   @csrf_exempt
   @transaction.atomic
   def post(self, request: HttpRequest):
      user_id = request.POST.get("store_owner")
      
      # VERIFY USER EXISTENCE
      user_exists = get_user_or_none(user_id)
      
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
         'Content-Type': "application/json",
         'Authorization': f'Bearer {settings.TEST_SECRET_KEY}'
      }
      # Get User Data
      user = self.collect_user(request)
      amount = 500000

      payload = {
         "email": user.email,
         "amount": amount,
         "channels": ["card"]
      }

      response = requests.post(url, headers=headers, json=payload)
      if response.status_code == 200:
         data = response.json()
         return Response(data, status=status.HTTP_200_OK)
      else:
         return Response({"message": f"{response.text}"}, status=response.status_code)

   def collect_user(self, request: HttpRequest):
      user_id = request.data.get("store_owner")
      user_exists = get_user_or_none(user_id)
      if user_exists:
         return user_exists
      else:
         raise ValueError("Invalid store owner user ID.")


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
         return Response({"message": f'{response_data}'}, status=response.status_code)
