from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mall.models import Wallet
import requests
import datetime
import uuid
import logging


logger = logging.getLogger(__name__)
# SECRET_KEY = env("TEST_KEY")

class PayoutDropshipper(APIView):
    def post(self, request):
        customer = request.user
        try:
            with transaction.atomic():
                wallet = self.get_dropshipper_wallet(customer)
                if wallet:
                    response = self.make_transfer(wallet)
                    # logger.info("An error occurred", exc_info=True)
                    print(response.text)
                    return Response(response.json(), status=response.status_code)
                
                else:
                    return Response({"message": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("An error occurred: %s", e, exc_info=True)
            return Response({"message": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_dropshipper_wallet(self, customer):
        """Get the dropshipper's wallet balance to make their transfer to their account"""
        store_id = customer.owners.id
        try:
            wallet = Wallet.objects.select_for_update().get(store=store_id)
            return wallet
        except Wallet.DoesNotExist:
            return None

    def make_transfer(self, wallet):
        """Make transfer to dropshipper's account"""
        headers = { 
            'content-type': 'application/json',
            'Authorization': 'Bearer FLWSECK_TEST-58b95a6e53a8e57b3a63fb3d48626388-X'
        }
        url = 'https://api.flutterwave.com/v3/transfers'
        
        data =  {
            "account_bank": str(wallet.bank_code),
            "account_number": str(wallet.nuban),
            "amount": int(wallet.balance),
            "narration": f"RockTea Mall Payout -- {datetime.datetime.now()}",
            "currency": "NGN",
            "reference": self.generate_tx_ref(),
            "callback_url": "https://www.flutterwave.com/ng/",
            "debit_currency": "NGN"
        }
        
        response = requests.post(url, headers=headers, json=data)
        # print(int(wallet.balance))
        return response

    def generate_tx_ref(self):
        """Generate a unique transaction reference using timestamp and UUID"""
        timestamp = str(int(datetime.datetime.now().timestamp()))
        uid = str(uuid.uuid4().hex)
        tx_ref ="RCKT_MALL-" + timestamp + "_" + uid
        return tx_ref