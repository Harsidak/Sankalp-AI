from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

class MemoryService:
    def __init__(self):
        self.max_history_tokens = 4000 # Approximation
        self.max_messages = 20
        
    def trim_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Trims the history to fit within context limits.
        Simple strategy: Keep system prompt (if any, usually passed separate), 
        keep last N messages.
        """
        if len(history) <= self.max_messages:
            return history
            
        # Keep the most recent messages
        trimmed = history[-self.max_messages:]
        
        # Ensure the first message in trimmed block isn't a lonely 'model' response if strictly alternating?
        # Gemini is flexible, but generally User/Model/User/Model is best.
        # If first is model, maybe cut it?
        if trimmed and trimmed[0].get('role') == 'model':
             # Try to keep pairs if possible, or just accept it.
             pass
             
        logger.info("History trimmed", original_count=len(history), new_count=len(trimmed))
        return trimmed

    def summarize_context(self, context: str) -> str:
        # Placeholder for summarization logic
        pass

memory_service = MemoryService()
