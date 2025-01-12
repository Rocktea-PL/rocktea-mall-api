import datetime
import uuid
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

def initiate_payment(email, amount, user_id, base_url):
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    amount = float(amount)
    amount_in_naira = amount * 100
    data = {
        'email': email,
        'amount': amount_in_naira,
        'callback_url': base_url,
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

def get_bank_list_paystack():
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    url = f'https://api.paystack.co/bank?currency=NGN'
    
    response = requests.get(url, headers=headers)
    return response.json()

def get_account_name_paystack(account_number, bank_code):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    url = f'https://api.paystack.co/bank/resolve?account_number={account_number}&bank_code={bank_code}'
    
    response = requests.get(url, headers=headers)
    return response.json()

def get_receipient_code_transfer_paystack(body_data):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    url = f'https://api.paystack.co/transferrecipient'

    data = {
        'type':             'nuban',
        'name':             body_data['name'],
        'account_number':   body_data['account_number'],
        'bank_code':        body_data['bank_code'],
        'currency':         'NGN'
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def initiate_transfer_paystack(transfer_data):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    url = f'https://api.paystack.co/transfer'

    amount = int(transfer_data['amount'])
    amount_in_naira = amount * 100

    data = {
        'source':       'balance',
        'reason':       'profit from rocktea',
        'amount':       amount_in_naira,
        'reference':    generate_tx_ref(),
        'recipient':    transfer_data['recipient_code']
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def otp_transfer_paystack(transfer_data):
    headers = { 
        'content-type': 'application/json',
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }
    url = f'https://api.paystack.co/transfer/finalize_transfer'

    data = {
        'transfer_code':    transfer_data['transfer_code'],
        'otp':              transfer_data['otp']
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def generate_tx_ref():
    """Generate a unique transaction reference using timestamp and UUID"""
    timestamp = str(int(datetime.datetime.now().timestamp()))
    uid = str(uuid.uuid4().hex)
    tx_ref ="RCKT_MALL-" + timestamp + "_" + uid
    return tx_ref