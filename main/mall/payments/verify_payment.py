from rest_framework.decorators import api_view
from rest_framework.response import Response
import environ, requests

env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env("TEST_KEY")


@api_view(["GET"])
def verify_payment(request, transaction_id):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {SECRET_KEY}'
    }
    url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'
    
    response = requests.get(url, headers=headers)
    return Response(response.json())
