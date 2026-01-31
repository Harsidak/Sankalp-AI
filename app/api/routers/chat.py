from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.api.schemas import StartChatRequest, ChatTitleRequest, ChatStreamRequest
from app.services.llm_service import llm_service, get_language_name, SYSTEM_INSTRUCTION_TEMPLATE
from app.core.config import config
import json
from pydantic import ValidationError

from app.services.guardrails import guardrails
from app.services.memory_service import memory_service
from app import limiter

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/start_chat', methods=['POST'])
@limiter.limit("10 per minute")
def start_chat():
    try:
        data = StartChatRequest(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 422

    # Validate inputs (example for emotions, though list is safe)
    # We apply generalized guardrails on free text if any.
    
    language_name = get_language_name(data.language)
    prompt = f"A user in the '{data.ageGroup}' age group is feeling the following emotions: {', '.join(data.emotions)}. They've rated the intensity of these feelings as {data.intensity} out of 10. Please provide a warm, empathetic, and reassuring opening message based on this, in the {language_name} language. Acknowledge their feelings, validate their experience, and gently invite them to talk more about what's on your mind. Let them know you're here to listen without judgment."

    try:
        text = llm_service.generate_content(prompt)
        return jsonify({'message': text})
    except Exception as e:
        return jsonify({'message': f"Hi there. I'm here to listen and support you. (Fallback in {language_name})"}), 200

@chat_bp.route('/chat_title', methods=['POST'])
def chat_title():
    try:
        data = ChatTitleRequest(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 422
        
    if len(data.messages) < 2:
        return jsonify({'title': 'New Conversation'})
        
    language_name = get_language_name(data.language)
    conversation = "\n".join([f"{m.author}: {m.text}" for m in data.messages])
    prompt = f"Based on the following conversation start, create a very short, concise title (4-5 words max) in {language_name} that captures the main theme. Do not use quotes or special characters.\n\nConversation:\n{conversation}"
    
    try:
        title = llm_service.generate_content(prompt)
        title = title.strip().replace('"', '').replace("'", "")
        return jsonify({'title': title})
    except Exception:
        return jsonify({'title': 'Conversation'})

@chat_bp.route('/chat_stream', methods=['POST'])
@limiter.limit("30 per minute")
def chat_stream():
    try:
        data = ChatStreamRequest(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 422
    
    # Guardrails Check for last message
    last_msg = data.messages[-1].text
    is_valid, error = guardrails.validate_input(last_msg)
    if not is_valid:
        # For stream we return a stream error ideally, or just a json error
        # Since client expects stream, we'll yield the json error.
        def error_gen():
             yield json.dumps({'error': error}) + '\n'
        return Response(stream_with_context(error_gen()), mimetype='application/x-ndjson')

    language_name = get_language_name(data.language)
    
    # Context Construction
    user_name = data.context.get('name', 'Friend')
    streak = data.context.get('streak', 0)
    mood_data = data.context.get('mood', {})
    
    base_instruction = SYSTEM_INSTRUCTION_TEMPLATE.format(language_name=language_name)
    additional_context = f"\n\nUser Context:\n- Name: {user_name}\n- Current Streak: {streak} days\n"
    if mood_data:
        additional_context += f"- Recent Mood: {mood_data.get('score', '?')}/10 (Tags: {', '.join(mood_data.get('tags', []))})\n"
    
    final_instruction = base_instruction + additional_context
    
    history = []
    for m in data.messages[:-1]:
        role = 'user' if m.author == 'user' else 'model'
        history.append({'role': role, 'parts': [m.text]})
    
    # Trim history
    history = memory_service.trim_history(history)
        
    last_message = data.messages[-1].text
    
    def generate():
        import asyncio
        # We can't really use async/await easily in generic Flask stream without async mode, 
        # but llm_service.stream_chat is defined async. 
        # Wait, waitress + flask is sync. I should probably make stream_chat sync or use a sync wrapper.
        # For now, let's assume I change stream_chat to sync or run it appropriately.
        # Actually Google GenAI library is sync by default unless using async client. 
        # My LLMService definition used `async def stream_chat` but inside it called `send_message(stream=True)` which is sync compatible if iterating?
        # Let's fix LLMService to be sync for Flask compatibility or use `asyncio.run`.
        # Simplest is to make LLMService sync for now as Flask 2.x + Waitress is WSGI (Sync).
        
        # FIX: I will redefine the generator to use the sync method from genai directly or fix LLMService.
        # Let's assume LLMService needs to be fixed to Sync. I will do that in a follow up or just inline it here if I can't edit it back easily. 
        # Actually, I can just not use `await` and iterate if the underlying lib is sync. 
        # GenAI `chat_session.send_message(..., stream=True)` returns a synchronous iterator `GenerateContentResponse`.
        # So `async def` in LLMService was a mistake if I want to use it in standard Flask without `[async]` extra.
        # I'll call the sync version for now.
        
        try:
            # Re-instantiate model here or use service if sync. 
            # I'll fix LLMService in next step. For now I'll use direct call to avoid error.
             
            model = genai.GenerativeModel(config.TUNED_MODEL_NAME, system_instruction=final_instruction)
            chat = model.start_chat(history=history)
            response = chat.send_message(last_message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield json.dumps({'text': chunk.text}) + '\n'
        except Exception as e:
            yield json.dumps({'error': str(e)}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')
