import requests
import logging
import os


logger = logging.getLogger(__name__)


def verify_bvn(bvn):
    try:
        url = "https://api.dojah.io/api/v1/kyc/bvn/full"

        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        params = {
            "bvn": bvn
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f'verify_bvn@error: {response.status_code} - {response.text}')
            return False, response.json()

        return True, response.json()

    except Exception as e:
        logger.error('verify_bvn@error')
        logger.error(e)
        return False, None


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

        params = {
            "nin": nin
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f'verify_nin@error: {response.status_code} - {response.text}')
            return False, response.json()

        return True, response.json()

    except Exception as e:
        logger.error('verify_nin@error')
        logger.error(e)
        return False, None


def verify_drivers_licence(license_number):
    try:
        url = "https://api.dojah.io/api/v1/kyc/dl"

        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        params = {
            "license_number": license_number
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f'verify_drivers_licence@error: {response.status_code} - {response.text}')
            return False, response.json()

        return True, response.json()

    except Exception as e:
        logger.error('verify_drivers_licence@error')
        logger.error(e)
        return False, None


def verify_voter_id(vin):
    try:
        url = "https://api.dojah.io/api/v1/kyc/vin"

        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        params = {
            "vin": vin
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f'verify_voter_id@error: {response.status_code} - {response.text}')
            return False, response.json()

        return True, response.json()

    except Exception as e:
        logger.error('verify_voter_id@error')
        logger.error(e)
        return False, None


def verify_international_passport(passport_number, surname):
    try:
        url = "https://api.dojah.io/api/v1/kyc/passport"

        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        params = {
            "passport_number": passport_number,
            "surname": surname
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f'verify_international_passport@error: {response.status_code} - {response.text}')
            return False, response.json()

        return True, response.json()

    except Exception as e:
        logger.error('verify_international_passport@error')
        logger.error(e)
        return False, None


def verify_cac(rc_number, company_name):
    try:
        url = "https://api.dojah.io/api/v1/kyc/cac"

        # Fetch the API key from environment variables
        api_key = os.getenv('DOJAH_API_KEY')
        app_id = os.getenv('DOJAH_APP_ID')

        headers = {
            "accept": "application/json",
            "Authorization": api_key,
            "AppId": app_id
        }

        params = {
            "company_name": company_name,
            "rc_number": rc_number
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f'verify_cac@error: {response.status_code} - {response.text}')
            return False, response.json()

        return True, response.json()

    except Exception as e:
        logger.error('verify_cac@error')
        logger.error(e)
        return False, None
