import os
import json
import time
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
import google.generativeai as genai
from waitress import serve

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("VITE_GEMINI_API_KEY")
model_name = os.getenv("TUNED_MODEL_NAME") or "gemini-2.5-flash"

if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")

# Constants
LANGUAGES = [
    {'code': 'en', 'name': 'English'},
    {'code': 'hi', 'name': 'Hindi'},
    {'code': 'es', 'name': 'Spanish'},
    {'code': 'fr', 'name': 'French'},
    {'code': 'de', 'name': 'German'},
    {'code': 'it', 'name': 'Italian'},
    {'code': 'pt', 'name': 'Portuguese'},
    {'code': 'ru', 'name': 'Russian'},
    {'code': 'ja', 'name': 'Japanese'},
    {'code': 'ko', 'name': 'Korean'},
    {'code': 'zh', 'name': 'Chinese'},
]

EMOTIONS = [
    {'key': 'uplifting', 'en': 'Uplifting'},
]

SYSTEM_INSTRUCTION_TEMPLATE = """You are Sankalp, a compassionate, empathetic, and supportive AI mental health assistant designed for young people. Your primary goal is to provide a safe, non-judgmental space for users to express their feelings. Use simple, encouraging, and age-appropriate language. You should actively listen, validate their feelings, and offer gentle guidance and coping strategies. Do NOT provide medical advice or medical drug, diagnoses, or clinical terminology. If a user expresses thoughts of self-harm or is in immediate danger, gently but clearly encourage them to speak to a trusted adult, a crisis hotline, or emergency services immediately. Your persona is warm, patient, and understanding, like a supportive older sibling or a trusted mentor. Your response MUST be exclusively in {language_name}. Do not switch languages under any circumstances.
Make sure to detect the situation and emotions the user is facing.
If the user express negative emotions:
- Start with comfort and validation.
- Ask for details if needed.
- Ask about substance use or medical conditions gently if relevant.
- Ask about thoughts of self-harm if safety is a concern.
- Speak in a loving, supportive way.
If the user express positive emotions:
- Acknowledge and celebrate.
- Encourage sharing more.
- Reinforce positive coping.

Respond in a cheerful, encouraging tone without being overbearing.
"""

def get_language_name(code):
    for lang in LANGUAGES:
        if lang['code'] == code:
            return lang['name']
    return 'English'
 
@app.context_processor
def inject_firebase_config():
    return dict(firebase_config={
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'databaseURL': os.getenv("FIREBASE_DATABASE_URL"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    })

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/start_chat', methods=['POST'])
def start_chat():
    data = request.json
    age_group = data.get('ageGroup')
    emotions = data.get('emotions', [])
    intensity = data.get('intensity', 5)
    language_code = data.get('language', 'en')
    
    language_name = get_language_name(language_code)
    
    prompt = f"A user in the '{age_group}' age group is feeling the following emotions: {', '.join(emotions)}. They've rated the intensity of these feelings as {intensity} out of 10. Please provide a warm, empathetic, and reassuring opening message based on this, in the {language_name} language. Acknowledge their feelings, validate their experience, and gently invite them to talk more about what's on your mind. Let them know you're here to listen without judgment."
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text = response.text
        return jsonify({'message': text})
    except Exception as e:
        print(f"Error generating initial message: {e}")
        return jsonify({'message': f"Hi there. I'm here to listen and support you. (Fallback in {language_name})"}), 200

@app.route('/api/chat_title', methods=['POST'])
def chat_title():
    data = request.json
    messages = data.get('messages', [])
    language_code = data.get('language', 'en')
    language_name = get_language_name(language_code)
    
    if len(messages) < 2:
        return jsonify({'title': 'New Conversation'})
        
    conversation = "\n".join([f"{m['author']}: {m['text']}" for m in messages])
    prompt = f"Based on the following conversation start, create a very short, concise title (4-5 words max) in {language_name} that captures the main theme. Do not use quotes or special characters.\n\nConversation:\n{conversation}"
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        title = response.text.strip().replace('"', '').replace("'", "")
        return jsonify({'title': title})
    except Exception as e:
        print(f"Error generating title: {e}")
        return jsonify({'title': 'Conversation'})

@app.route('/api/chat_stream', methods=['POST'])
def chat_stream():
    data = request.json
    messages = data.get('messages', [])
    language_code = data.get('language', 'en')
    language_name = get_language_name(language_code)
    
    contents = []
    system_instruction = SYSTEM_INSTRUCTION_TEMPLATE.format(language_name=language_name)
    
    for m in messages[:-1]:
        role = 'user' if m['author'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [m['text']]})
        
    last_message = messages[-1]['text']
    
    model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
    
    def generate():
        try:
            chat_session = model.start_chat(history=contents)
            response = chat_session.send_message(last_message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield json.dumps({'text': chunk.text}) + '\n'
        except Exception as e:
            print(f"Error in chat stream: {e}")
            yield json.dumps({'error': str(e)}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

@app.route('/api/wellness_plan', methods=['POST'])
def wellness_plan():
    data = request.json
    language_code = data.get('language', 'en')
    language_name = get_language_name(language_code)
    
    prompt = f"""You are an expert wellness coach. Create a personalized, gamified self-care plan for the user.
    generate a generic plan suitable for a young person.
    Tasks:
    1. Create a single, realistic **daily challenge**.
    2. Suggest a **reward** for it (type: 'points', 'badge', or 'milestone').
    3. Design a **streak system**: State current streak, 7-day reward, and encouragement.
    4. Offer a short, general **encouragement message**.
    5. Generate a **weekly challenge** with a reward and a specific 'goalDays' (number between 3-7).
    The challenges must be calming and simple due to stress. Be supportive.
    Return ONLY the specified JSON. All text in the response must be in {language_name}.
    Schema:
    {{
      "dailyChallenge": {{ "description": "string", "reward": {{ "type": "string", "value": "string" }} }},
      "streakInfo": {{ "currentStreak": number, "reward": "string", "encouragement": "string" }},
      "weeklyChallenge": {{ "description": "string", "reward": {{ "type": "string", "value": "string" }}, "goalDays": number }},
      "encouragement": "string"
    }}
    """
    
    try:
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        return Response(response.text, mimetype='application/json')
    except Exception as e:
        print(f"Error generating wellness plan: {e}")
        return jsonify({"error": "Failed to generate plan"}), 500

@app.route('/api/dashboard_analytics', methods=['POST'])
def dashboard_analytics():
    data = request.json
    language_code = data.get('language', 'en')
    language_name = get_language_name(language_code)
    
    prompt = f"""You are a data synthesizer for a wellness app. Generate a realistic but mock analytics summary for a user.
    Your Tasks:
    1.  **keyMetrics**: Create an object with 'currentStreak' (number between 2-10) and 'challengesCompleted' (number between 5-20).
    2.  **moodTrend**: Create an array of 7 objects. Each object should have a 'day' (e.g., "Mon", "Tue") and a 'moodScore' (a number between 1 and 10, showing some variation).
    3.  **emotionBreakdown**: Create an array of 3-4 objects. Each object should have an 'emotion', a 'percentage' (all percentages must sum to 100), and a 'color' (a hex code like '#8B5CF6').
    4.  **activityLog**: Create an array of 2-3 recent activity objects. Each should have a 'date' and an 'activity'.
    
    Return ONLY the specified JSON. All text fields (emotion, date, activity) must be in {language_name}.
    Schema:
    {{
        "keyMetrics": {{ "currentStreak": number, "challengesCompleted": number }},
        "moodTrend": [ {{ "day": "string", "moodScore": number }} ],
        "emotionBreakdown": [ {{ "emotion": "string", "percentage": number, "color": "string" }} ],
        "activityLog": [ {{ "date": "string", "activity": "string" }} ]
    }}
    """
    
    try:
        model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        return Response(response.text, mimetype='application/json')
    except Exception as e:
        print(f"Error generating analytics: {e}")
        return jsonify({"error": "Failed to generate analytics"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting production server on http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port)
