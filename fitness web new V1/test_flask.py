from flask import Flask, jsonify
import os
from dotenv import load_dotenv
import openai

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/test')
def test():
    try:
        # Test OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=5
        )
        return jsonify({
            "status": "success",
            "response": response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
