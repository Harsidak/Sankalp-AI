import re
import structlog
from typing import Tuple, Optional

logger = structlog.get_logger()

class Guardrails:
    def __init__(self):
        # detailed pattern matching for potential injections
        self.injection_patterns = [
            r"ignore previous instructions",
            r"system prompt",
            r"you are not",
            r"delete user",
            r"drop table",
        ]
        
    def validate_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validates user input. Returns (is_valid, error_message).
        """
        if not text:
            return False, "Input cannot be empty."
            
        if len(text) > 1000: # Reasonable limit for chat message
            return False, "Input text is too long."
            
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("Potential injection detected", text=text, pattern=pattern)
                return False, "I cannot process that request."
                
        return True, None

    def sanitize(self, text: str) -> str:
        """
        Basic sanitization.
        """
        return text.strip()

guardrails = Guardrails()
