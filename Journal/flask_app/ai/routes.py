from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
import google.generativeai as genai
import os
from dotenv import load_dotenv
from ..models import JournalEntry  # Updated import to use JournalEntry instead of Journal
from cryptography.fernet import InvalidToken # Import the specific exception

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

        # Fetch all journal entries for the current user using MongoEngine syntax
        user_entries = JournalEntry.objects(user=current_user.id).order_by('-created_at').all()

        # Process entries, handling potential decryption errors individually
        past_entries_parts = []
        for entry in user_entries:
            try:
                decrypted_content = entry.decrypt_content()
                past_entries_parts.append(f"Date: {entry.created_at.strftime('%Y-%m-%d')}\\n{decrypted_content}")
            except InvalidToken:
                # Handle entries that cannot be decrypted (e.g., due to old salt)
                print(f"Warning: Could not decrypt entry with ID {entry.id} created at {entry.created_at}. Skipping.")
                past_entries_parts.append(f"Date: {entry.created_at.strftime('%Y-%m-%d')}\\n[Content could not be decrypted]")
            except Exception as decrypt_err:
                # Catch other potential errors during decryption
                print(f"Warning: Error processing entry ID {entry.id}: {repr(decrypt_err)}")
                past_entries_parts.append(f"Date: {entry.created_at.strftime('%Y-%m-%d')}\\n[Error processing content]")

        all_entries_text = "\\n---\\n".join(past_entries_parts)

        # Create a refined prompt to generate an alternative perspective, including past entries
        prompt = (
            f"You are an empathetic perspective-giving assistant helping users see different viewpoints about their journal entries."
            f"You guide the user, show them the way, give them wise advice. Try your best toanalyze common patterns in the past entries, mention them in your response and use user's past to guide them\\n"
            f"Given the following recent journal entry AND the user's past entries, provide one concise alternative perspective or insight that might help the user about their MOST RECENT entry ({text})."
            f"The perspective must:\\n"
            f"1. Offer a compassionate, alternative way of looking at the situation described in the MOST RECENT entry.\\n"
            f"2. Consider the context of past entries if relevant, but focus on the recent one.\\n"
            f"3. Highlight potential positive aspects or growth opportunities related to the recent entry.\\n"
            f"4. Be validating and non-judgmental of the user's experience.\\n\\n"
            f"MOST RECENT Journal entry:\\n{text}\\n\\n"
            f"--- PAST ENTRIES --- \\n{all_entries_text}\\n--- END PAST ENTRIES ---"
        )

        # Generate responses
        response = model.generate_content(prompt)

        # Return the response as JSON
        return jsonify({"perspective": response.text})
    except Exception as e:
        # Improved error logging
        print(f"Error in /get-perspective: {str(e)} ({repr(e)})")
        # Also print traceback for more context
        import traceback
        traceback.print_exc()
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

