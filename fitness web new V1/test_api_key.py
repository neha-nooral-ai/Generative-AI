import google.generativeai as genai

def test_gemini_api(api_key):
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Test a simple prompt
        response = model.generate_content("Hello, can you tell me what 2+2 is?")
        
        print("✅ API Key is working!")
        print("Response:", response.text)
        return True
        
    except Exception as e:
        print("❌ Error with API Key:")
        print(str(e))
        return False

if __name__ == "__main__":
    # Replace this with your actual API key
    API_KEY = "AIzaSyDhazrR7Z_BBVDlTJn13duVcBNG17yVtt8"
    
    print("Testing Gemini API Key...")
    test_gemini_api(API_KEY)
