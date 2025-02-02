from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from chatbot import initialize_agent
from langchain_core.messages import HumanMessage

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/chat', methods=['POST', 'OPTIONS'])
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