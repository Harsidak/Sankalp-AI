from flask import Blueprint, request, jsonify, Response
from app.api.schemas import DashboardAnalyticsRequest
from app.services.llm_service import llm_service, get_language_name
from pydantic import ValidationError

from app import limiter

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard_analytics', methods=['POST'])
@limiter.limit("10 per minute")
def dashboard_analytics():
    try:
        data = DashboardAnalyticsRequest(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 422
        
    language_name = get_language_name(data.language)
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
        text = llm_service.generate_content(prompt, json_mode=True)
        return Response(text, mimetype='application/json')
    except Exception as e:
        return jsonify({"error": "Failed to generate analytics"}), 500
