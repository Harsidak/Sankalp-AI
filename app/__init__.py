from flask import Flask
from .core.config import config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from app.core.logging_config import configure_logging
from app.core.middleware import register_logging_middleware

configure_logging()

limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
    app.config.from_object(config)
    
    # Initialize Extensions
    limiter.init_app(app)
    register_logging_middleware(app)
    
    # Register Blueprints
    from .api.routers.pages import pages_bp
    from .api.routers.chat import chat_bp
    from .api.routers.wellness import wellness_bp
    from .api.routers.dashboard import dashboard_bp
    
    app.register_blueprint(pages_bp)
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(wellness_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    
    @app.context_processor
    def inject_firebase_config():
        return dict(firebase_config={
            'apiKey': config.FIREBASE_API_KEY,
            'authDomain': config.FIREBASE_AUTH_DOMAIN,
            'databaseURL': os.getenv("FIREBASE_DATABASE_URL"),
            'projectId': config.FIREBASE_PROJECT_ID,
            'storageBucket': config.FIREBASE_STORAGE_BUCKET,
            'messagingSenderId': config.FIREBASE_MESSAGING_SENDER_ID,
            'appId': config.FIREBASE_APP_ID,
            'measurementId': config.FIREBASE_MEASUREMENT_ID
        })

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # HSTS - Enable in production with SSL
        if config.ENV == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    return app
