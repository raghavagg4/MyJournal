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
            model = genai.GenerativeModel('gemini-2.0-flash-lite-preview')

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
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        # Get the text from either GET or POST request
        if request.method == "GET":
            text = request.args.get('text', '')
        else:
            data = request.get_json()
            text = data.get('text', '')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Create a refined prompt to generate thought-provoking questions
        prompt = (
    "You are an insightful reflection assistant helping users delve deeper into their journal entries. "
    "Given the following journal entry, generate one concise, thought-provoking question to encourage deeper reflection. "
    "The question must:\n"
    "1. Directly relate to the specific content and emotions expressed.\n"
    "2. Encourage exploration of underlying thoughts, feelings, or motivations.\n"
    "3. Aknowledge the user's emotions, thoughts, and feelings.\n"
    "4. Keep the question simple and concise (no more than 15 words).\n"
    "5. If it helps, try to give user a situation to relfect on\n"
    f"Journal entry: {text}\n")

        # Generate responses
        response = model.generate_content(prompt)

        # Return the response as JSON
        return jsonify({"question": response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ai.route("/get-perspective", methods=["GET", "POST"])
@login_required
def get_perspective():
    try:
        # Initialize the model with the latest version
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        # Get the text from either GET or POST request
        if request.method == "GET":
            text = request.args.get('text', '')
        else:
            data = request.get_json()
            text = data.get('text', '')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Create a refined prompt to generate an alternative perspective
        prompt = (
    "You are an empathetic perspective-giving assistant helping users see different viewpoints about their journal entries."
    "You guide the user, show them the way, give them wise advice."
    "Given the following journal entry, provide one concise alternative perspective or insight that might help the user. "
    "The perspective must:\n"
    "1. Offer a compassionate, alternative way of looking at the situation.\n"
    "2. Highlight potential positive aspects or growth opportunities not mentioned.\n"
    "3. Be validating and non-judgmental of the user's experience.\n"
    f"Journal entry: {text}\n")

        # Generate responses
        response = model.generate_content(prompt)

        # Return the response as JSON
        return jsonify({"perspective": response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ai.route('/get-whispers', methods=["GET", "POST"])
@login_required
def get_whispers():
    try:
        # Get the text from either GET or POST request
        if request.method == "GET":
            text = request.args.get('text', '')
        else:  # POST request
            data = request.get_json()
            text = data.get('text', '')

        # Initialize Gemini API with the same model as other routes
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        # Create a prompt for the Gemini API - Updated for "Get Direction"
        prompt = f"""You are a thoughtful guide helping someone journal. Based on their previous entry (if any), ask a fresh, engaging question that encourages reflection and exploration of new topics.
Just aks the question. don't include anything else in your repsonse. The question should be simple.
        Previous Entry:
        {text}

        If the previous entry is empty, respond with something like "How was your day today?"
        Otherwise, generate a new question that explores a different aspect or topic than what was discussed before.

        Response should be a single clear question that invites reflection. Just aks the question. don't include anything else in your repsonse. """

        # Generate response
        response = model.generate_content(prompt)

        return jsonify({'direction': response.text})

    except Exception as e:
        print(f"Error in get_whispers: {str(e)}")
        return jsonify({'error': 'Failed to generate whispers'}), 500

