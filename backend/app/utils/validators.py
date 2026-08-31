"""
Input validation utilities.
"""

import re
from typing import Optional


def validate_password_strength(password: str) -> Optional[str]:
    """
    Validate password meets minimum strength requirements.

    Returns None if valid, or an error message string if invalid.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return "Password must contain at least one digit"
    return None


def validate_email_format(email: str) -> bool:
    """Basic email format validation (Pydantic EmailStr handles most cases)."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
