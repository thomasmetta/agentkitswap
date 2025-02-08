from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from chatbot import initialize_agent
from langchain_core.messages import HumanMessage
from functools import wraps
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv() 
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key') 
CORS(app, origins=["http://localhost:3000"])

def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow OPTIONS request to pass through for CORS
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Verify the token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # You can add additional checks here (e.g., user validation)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    # In a real application, you would verify credentials here
    # For demo purposes, we're just generating a token
    token = jwt.encode({
        'user_id': 'demo_user',
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'])
    
    return jsonify({'token': token})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/chat', methods=['POST', 'OPTIONS'])
@require_jwt
def chat_endpoint():
    if request.method == "OPTIONS":
        return make_response("OK", 200)
        
    """Handle chat requests from the React frontend."""
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    agent_executor, config = initialize_agent()
    responses = []
    
    try:
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=user_input)]}, config
        ):
            if "agent" in chunk:
                responses.append(chunk["agent"]["messages"][0].content)
            elif "tools" in chunk:
                responses.append(chunk["tools"]["messages"][0].content)
        
        return jsonify({'responses': responses})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5001) 