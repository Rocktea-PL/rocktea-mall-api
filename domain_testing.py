import requests

def verify_tin(self, request):
    url = "https://api.appruve.co/v1/verifications/ng/tin"

    data = {
        "id": "00000001-0000",
        "name": "John Doe Inc.",
        "email": "john.doe@gmail.com",
        "phone_number": "+234000000000",
        "registration_number": "",
        "tax_office": ""
    }

    # Replace 'YOUR_BEARER_TOKEN' with your actual bearer token
    bearer_token = 'eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5hcHBydXZlLmNvIiwianRpIjoiMjEyZWIyNjMtYzIyZS00NzEwLThjODUtMDExM2FmY2MwZDUzIiwiYXVkIjoiZmM4OTM3YjktYTM0Yi00OWY3LWJlOWEtYTM5ODVhMWYzNjQ2Iiwic3ViIjoiY2Q4YjUwZGYtODFkNC00MmIzLTliNjAtMDgzODhmNjkwMThmIiwibmJmIjowLCJzY29wZXMiOlsidmVyaWZpY2F0aW9uX3ZpZXciLCJ2ZXJpZmljYXRpb25fbGlzdCIsInZlcmlmaWNhdGlvbl9kb2N1bWVudCIsInZlcmlmaWNhdGlvbl9pZGVudGl0eSJdLCJleHAiOjMyNzE5MzcwMTEsImlhdCI6MTY5NDAxMzgxMX0.NjT49_v6eX7cuJlABYSgvRw5O9B7oPi54dMBLbDGL30'


    headers = {
        'Authorization': f'Bearer {bearer_token}',  # Add Bearer token as header
        'Content-Type': 'application/json'  # Specify the content type
    }

    # Send the POST request with the JSON payload
    response = requests.post(url, json=data, headers=headers)

    # Print the response content to the terminal
    print(response.text)  # This will print the response content as a string

    return response 