from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

ai = Blueprint("ai", __name__)

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

@ai.route("/ai-assistant", methods=["GET", "POST"])
@login_required
def ai_assistant():
    if request.method == "POST":
        try:
            # Initialize the model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Get the message from the request
            data = request.get_json()
            message = data.get('message', "Hello, I'm your AI assistant. How can I help you today?")
            
            # Generate response
            response = model.generate_content(message)
            
            return jsonify({"response": response.text})
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    return render_template("ai_assistant.html")

@ai.route("/go-deeper", methods=["GET", "POST"])
@login_required
def go_deeper():
    try:
        # Initialize the model with the latest version
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        # Get the text from either GET or POST request
        if request.method == "GET":
            text = request.args.get('text', '')
        else:
            data = request.get_json()
            text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Create a prompt to generate thought-provoking questions
        prompt = f"""Based on the following journal entry, generate a thought-provoking question that encourages deeper reflection. 
        The question should be relevant to the content and help the writer explore their thoughts and feelings more deeply.
        Keep the question concise and open-ended.
        
        Journal entry: {text}
        
        Question:"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return the response as JSON
        return jsonify({"question": response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500 