import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read variables
GRAPH_API_VERSION = "v20.0"
APP_ID = os.getenv("FB_CLIENT_ID")
APP_SECRET = os.getenv("FB_CLIENT_SECRET")
FB_EXCHANGE_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# Construct the URL
url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"
params = {
    "grant_type": "fb_exchange_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "fb_exchange_token": FB_EXCHANGE_TOKEN,
}

# Make the GET request
response = requests.get(url, params=params)

# Handle and print response
if response.status_code == 200:
    data = response.json()
    print("Long-Lived Access Token:", data.get("access_token"))
else:
    print("Error:", response.status_code)
    print(response.text)
