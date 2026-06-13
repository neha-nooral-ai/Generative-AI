import os
import sys
from dotenv import load_dotenv

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

# Load environment variables
load_dotenv()
print("Environment variables loaded")

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key exists: {bool(api_key)}")
print(f"API Key starts with: {api_key[:10] if api_key else 'N/A'}")

# Try importing OpenAI
try:
    print("\nAttempting to import OpenAI...")
    from openai import OpenAI
    print("OpenAI imported successfully")
    
    # Try initializing the client
    print("\nAttempting to initialize OpenAI client...")
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully")
    
    # Test a simple completion
    print("\nTesting API call...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=5
    )
    print("\nAPI Response:")
    print(response.choices[0].message.content)
    
except Exception as e:
    print("\nError:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\nModule attributes:", dir(e))
