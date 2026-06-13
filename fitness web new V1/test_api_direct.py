import requests
import json

# Your API key
API_KEY = "AIzaSyDhazrR7Z_bbVDlTJn13duVcBNG17yVtt8"

# The API endpoint for Gemini
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"

# The request headers
headers = {
    "Content-Type": "application/json"
}

# The request body
payload = {
    "contents": [{
        "parts": [{
            "text": "Hello, can you tell me what 2+2 is?"
        }]
    }]
}

try:
    # Make the request
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    # Check if the request was successful
    if response.status_code == 200:
        print("✅ API Key is valid!")
        print("Response:", response.json())
    else:
        print(f"❌ Error with API Key (Status Code: {response.status_code}):")
        print(response.text)
        
except Exception as e:
    print("❌ Error making request:")
    print(str(e))
