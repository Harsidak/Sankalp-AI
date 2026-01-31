from flask import Blueprint, request, jsonify, Response
from app.api.schemas import WellnessPlanRequest
from app.services.llm_service import llm_service, get_language_name
from pydantic import ValidationError

from app import limiter

wellness_bp = Blueprint('wellness', __name__)

@wellness_bp.route('/wellness_plan', methods=['POST'])
@limiter.limit("5 per minute")
def wellness_plan():
    try:
        data = WellnessPlanRequest(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 422
        
    language_name = get_language_name(data.language)
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
        text = llm_service.generate_content(prompt, json_mode=True)
        return Response(text, mimetype='application/json')
    except Exception as e:
        return jsonify({"error": "Failed to generate plan"}), 500
