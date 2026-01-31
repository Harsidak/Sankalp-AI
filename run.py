import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='google.generativeai')
from app import create_app
from app.core.config import config
from waitress import serve

app = create_app()

if __name__ == '__main__':
    print(f"Starting production server on http://0.0.0.0:{config.PORT}")
    serve(app, host='0.0.0.0', port=config.PORT)
