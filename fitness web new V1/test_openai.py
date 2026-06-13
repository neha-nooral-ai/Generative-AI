import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:10]}...")  # Print first 10 chars for security

# Initialize the client
try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully")
    
    # Test the connection
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, can you hear me?"}
        ],
        max_tokens=10
    )
    
    print("\nResponse from OpenAI:")
    print(response.choices[0].message.content)
    
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nTroubleshooting steps:")
    print("1. Check if your API key is valid")
    print("2. Check your internet connection")
    print("3. Try using a different network (some networks may block API calls)")
    print("4. Check if you have any proxy settings that might interfere")
