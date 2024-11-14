from rest_framework.decorators import api_view
from rest_framework.response import Response
from order.models import PaystackWebhook
import environ, requests

env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env("TEST_KEY")
PAYSTACK_SECRET_KEY = env("TEST_SECRET_KEY")


@api_view(["GET"])
def verify_payment(request, transaction_id):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {SECRET_KEY}'
    }
    url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'
    
    response = requests.get(url, headers=headers)
    return Response(response.json())

def initiate_payment(email, amount, user_id):
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    amount = int(amount)
    amount_in_naira = amount * 100
    data = {
        'email': email,
        'amount': amount_in_naira,
        'callback_url': 'https://rocktea-users.vercel.app/order_success',
        'metadata': {
            # 'store_id': store_id,
            'user_id': user_id
        }
    }
    url = 'https://api.paystack.co/transaction/initialize'
    
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    # Save the initializer data in PaystackWebhook
    if response_data['status']:
        PaystackWebhook.objects.create(
            user_id=user_id,
            # store_id=NULL,
            reference=response_data['data']['reference'],
            data=response_data,
            total_price=amount,
            status='Pending'
        )

    return response_data

# @api_view(["GET"])
def verify_payment_paystack(transaction_id):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    url = f'https://api.paystack.co/transaction/verify/{transaction_id}'
    
    response = requests.get(url, headers=headers)
    return Response(response.json())