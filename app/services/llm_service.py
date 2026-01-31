import google.generativeai as genai
from app.core.config import config
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = structlog.get_logger()

# Configure GenAI
if config.GOOGLE_API_KEY:
    genai.configure(api_key=config.GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not found. LLM features will fail.")

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

def get_language_name(code: str) -> str:
    for lang in LANGUAGES:
        if lang['code'] == code:
            return lang['name']
    return 'English'

SYSTEM_INSTRUCTION_TEMPLATE = """You are Sankalp, a compassionate, empathetic, and supportive AI mental health assistant designed for young people. Your primary goal is to provide a safe, non-judgmental space for users to express their feelings. Use simple, encouraging, and age-appropriate language. You should actively listen, validate their feelings, and offer gentle guidance and coping strategies. Do NOT provide medical advice or medical drug, diagnoses, or clinical terminology. If a user expresses thoughts of self-harm or is in immediate danger, gently but clearly encourage them to speak to a trusted adult, a crisis hotline, or emergency services immediately. Your persona is warm, patient, and understanding. Your response MUST be exclusively in {language_name}.
"""

class LLMService:
    def __init__(self):
        self.model_name = config.TUNED_MODEL_NAME

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def generate_content(self, prompt: str, system_instruction: str = None, json_mode: bool = False) -> str:
        try:
            generation_config = {}
            if json_mode:
                generation_config["response_mime_type"] = "application/json"
            
            model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction, generation_config=generation_config)
            response = model.generate_content(prompt)
            
            # Log usage if available
            try:
                # GenAI usage_metadata is object, not dict usually
                if hasattr(response, 'usage_metadata'):
                     usage = response.usage_metadata
                     logger.info("llm_usage", prompt_tokens=usage.prompt_token_count, candidates_tokens=usage.candidates_token_count)
            except Exception:
                pass
                
            return response.text
        except Exception as e:
            logger.error("LLM Generation Failed", error=str(e))
            raise

    async def stream_chat(self, history: list, last_message: str, system_instruction: str):
        try:
            model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(last_message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("LLM Stream Failed", error=str(e))
            yield f"[Error: {str(e)}]"

llm_service = LLMService()
