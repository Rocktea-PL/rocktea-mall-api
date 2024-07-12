import requests
import logging
import os


logger = logging.getLogger(__name__)


def verify_bvn(bvn):
    try:
        import requests

        url = "https://api.dojah.io/api/v1/kyc/bvn/full"
        
        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        response = requests.get(url, headers=headers)
        
        print(response.text)
        
        return response

    except Exception as e:
        logger.error('verify_bvn@error')
        logger.error(e)
        return None


def verify_nin(nin):
    try:
        url = "https://api.dojah.io/api/v1/kyc/nin"
        
        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        # Set the query parameters
        params = {
            "bvn": nin
        }

        response = requests.get(url, headers=headers, params=params)
        
        print(response.text)
        
        return response

    except Exception as e:
        logger.error('verify_nin@error')
        logger.error(e)
        return None


