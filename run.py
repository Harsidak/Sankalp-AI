import sys
import warnings

# Print immediately to show activity
print("Starting Sankalp AI System...", flush=True)

# Suppress all warnings from google.generativeai
warnings.filterwarnings("ignore", module='google.generativeai')

from app import create_app
from app.core.config import config
from waitress import serve

app = create_app()

if __name__ == '__main__':
    print(f"Server initialized. Listening on http://0.0.0.0:{config.PORT}", flush=True)
    serve(app, host='0.0.0.0', port=config.PORT)
