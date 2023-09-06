import requests
import json

url = 'https://client.harmonweb.com/includes/api.php'

data = {
    'action': 'DomainWhois',
    'username': 'JQXsYZqlcEkgMXhtWNdD95WCA3br4qDX',
    'password': 'W3fBNlVZekTolVAIg3IUSXTkL0QT3P8k',
    'domain': 'www.rockteapl.com',
    'responsetype': 'json',
}

# Convert the data to JSON format
data_json = json.dumps(data)

# Define the headers to specify JSON content
headers = {
    'Content-Type': 'application/json',
}

# Use the headers parameter to include headers in the request
response = requests.post(url, data=data_json, headers=headers)

# Check if the response status code indicates success (e.g., 200 OK)
if response.status_code == 200:
    if response.text.strip():  # Check if the response body is not empty
        try:
            # Attempt to parse the JSON response
            response_json = response.json()
            print(response_json)
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
    else:
        print("Response body is empty.")
else:
    print(f"Request failed with status code: {response.status_code}")
    print(response.text)
