import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())
    
    # AI Providers
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("VITE_GEMINI_API_KEY")
    TUNED_MODEL_NAME = os.getenv("TUNED_MODEL_NAME", "gemini-2.5-flash")
    
    # Firebase
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyB9V6jbdF08wDA4MOtkcWSw6i036YVKi94")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "sankalp-chatbot.firebaseapp.com")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "sankalp-chatbot")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "sankalp-chatbot.firebasestorage.app")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "132596670287")
    FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID", "1:132596670287:web:ef94b7c40ecb196024af3a")
    FIREBASE_MEASUREMENT_ID = os.getenv("FIREBASE_MEASUREMENT_ID", "G-2YPC9KMP6R")
    
    # App Settings
    PORT = int(os.environ.get("PORT", 8080))
    ENV = os.getenv("FLASK_ENV", "production")

config = Config()
