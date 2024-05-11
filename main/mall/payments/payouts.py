from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import environ, requests, uuid, datetime, time, logging
from rest_framework.views import APIView
from mall.models import Wallet
from django.shortcuts import get_object_or_404
from django.db import transaction

logger = logging.getLogger(__name__)
env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env("TEST_KEY")

    
class PayoutDropshipper(APIView):
    def post(self, request):
        customer = request.user
        try:
            with transaction.atomic():
                wallet = self.get_dropshipper_wallet(customer)
                if wallet:
                    headers = { 
                        'content-type': 'application/json',
                        'Authorization': f'Bearer FLWSECK_TEST-58b95a6e53a8e57b3a63fb3d48626388-X'
                    }
                    url = 'https://api.flutterwave.com/v3/transfers'
                    
                    data =  {
                        "account_bank": wallet.bank_code,
                        "account_number": wallet.nuban,
                        "amount": str(wallet.balance),
                        "narration": f"RockTea Mall Payout -- {datetime.datetime.now()}",
                        "currency": "NGN",
                        "reference": self.generate_tx_ref(),
                        "callback_url": f"https://{customer.owners.domain_name}",
                        "debit_currency": "NGN"
                    }
                    
                    response = requests.post(url, headers=headers, json=data)
                    return Response(response.json())
                else:
                    # Handle case when wallet is not found
                    return Response({"message": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Handle exception
            logger.error(str(e), exc_info=True)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_dropshipper_wallet(self, customer):
        """ GET the dropshipper's wallet balance to make their transfer to their account """
        store_id = customer.owners.id
        # print(store_id)
        wallet = Wallet.objects.select_for_update().get(store =store_id)
        return wallet
    
    def generate_tx_ref(self):
        """ Generate a unique transaction reference using timestamp and UUID """
        timestamp = str(int(datetime.datetime.now().timestamp()))
        uid = str(uuid.uuid4().hex)
        tx_ref = timestamp + "_" + uid
        return tx_ref