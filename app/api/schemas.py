from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    author: str
    text: str

class StartChatRequest(BaseModel):
    ageGroup: str = Field(..., description="Age group of the user")
    emotions: List[str] = Field(default_factory=list, description="List of emotions")
    intensity: int = Field(5, ge=1, le=10, description="Intensity of emotions 1-10")
    language: str = Field("en", description="ISO language code")

class ChatTitleRequest(BaseModel):
    messages: List[Message]
    language: str = "en"

class ChatStreamRequest(BaseModel):
    messages: List[Message]
    language: str = "en"
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class WellnessPlanRequest(BaseModel):
    language: str = "en"

class DashboardAnalyticsRequest(BaseModel):
    language: str = "en"
