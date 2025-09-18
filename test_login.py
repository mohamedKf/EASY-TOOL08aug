import requests

API_URL = "http://127.0.0.1:8000"  # Change if your Django server runs elsewhere

USERNAME = "sup1"  # change to your supplier username
PASSWORD = "1234"  # change to your supplier password

# Make login request
response = requests.post(
    f"{API_URL}/api/supplier/login/",
    json={"username": USERNAME, "password": PASSWORD}
)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
