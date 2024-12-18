import requests
from django.conf import settings
from datetime import datetime, timedelta
from django.core.cache import cache
import json

class ShipbubbleService:

    def __init__(self):
        self.api_key = settings.SHIPBUBBLE_API_KEY
        self.api_url = settings.SHIPBUBBLE_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def validate_address(self, shipment_data): 
        required_fields = ['phone', 'email', 'name', 'address'] 
        missing_fields = [field for field in required_fields if field not in shipment_data] 
        if missing_fields: 
            return { 'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}' } 
        url = f'{self.api_url}/shipping/address/validate' 
        response = requests.post(url, json=shipment_data, headers=self.headers) 
        return response.json()

    def get_rates(self, rate_data):
        url = f'{self.api_url}/shipping/fetch_rates'
        response = requests.post(url, json=rate_data, headers=self.headers)
        return response.json()
    
    def get_available_carrirers(self):
        url = f'{self.api_url}/shipping/couriers'
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_label_categories(self):
        url = f'{self.api_url}/shipping/labels/categories'
        response = requests.get(url, headers=self.headers)
        return response.json()

    def process_shipping(self, shipment_data, package_items):
        # Step 1: Validate Address
        validation_response = self.validate_address(shipment_data)
        if validation_response.get('status') != 'success':
            return {'status': 'error', 'message': 'shipping details is missing'}
        
        # Step 2: Get Rates
        sender_address_code = 64258701
        receiver_address_code = validation_response['data']['address_code']
        category_id = 77179563

        # Step 2: Get Rates
        rate_data = { 
            'sender_address_code': sender_address_code, 
            'reciever_address_code': receiver_address_code, 
            'pickup_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 
            'category_id': category_id, 
            'package_items': package_items, 
            'package_dimension': { 'length': 12, 'width': 10, 'height': 10 }, 
            'delivery_instructions': f'This package is to be delivered to {validation_response["data"]["name"]} at {validation_response["data"]["address"]}'
        }

        rates_response = self.get_rates(rate_data)
        if rates_response.get('status') != 'success':
            return {'status': 'error', 'message': 'Failed to retrieve shipping rates'}
            # return rates_response
        
        return rates_response

        # Step 3: Create Shipment
        # shipment_response = self.create_shipment(shipment_data)
        # return shipment_response

    def create_shipment(self, shipment_data, user_id):
        # Validate required fields 
        required_fields = ['request_token', 'service_code'] 
        missing_fields = [field for field in required_fields if field not in shipment_data] 
        if missing_fields: 
            return {'status': 'error', 'message': f'Missing required fields: {", ".join(missing_fields)}'}
        url = f'{self.api_url}/shipping/labels'
        response = requests.post(url, json=shipment_data, headers=self.headers)
        response_data = response.json()
        # Save feedback into cache 
        # cache.set(f'shipment_{rates_response["data"]["order_id"]}', rates_response, timeout=3600)
        cache.set(f'shipment_{user_id}', json.dumps(response_data), timeout=3600)
        return response.json()
    
    def track_shipping_status(self, order_ids):
        url = f'{self.api_url}/shipping/labels/list/{order_ids}'
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def cancelled_shipping_label(self, order_ids):
        url = f'{self.api_url}/shipping/labels/cancel/{order_ids}'
        response = requests.post(url, headers=self.headers)
        return response.json()