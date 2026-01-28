# Sankalp: AI Mental Health Companion

**Sankalp** is a compassionate, AI-powered mental health assistant designed specifically for students and youth. It provides a safe, non-judgmental space to express feelings, track emotional well-being, and build resilience through gamified challenges.

Built with a futuristic "Frosty Glass" UI, Sankalp combines advanced psychology with cutting-edge AI (Google Gemini) to offer real-time support in multiple languages.

## ✨ Key Features

*   **🤖 Empathetic AI Chat**:
    *   Powered by a **Custom Fine-Tuned Model on Vertex AI** (Specialized for Youth Mental Health).
    *   Provides validation, coping strategies, and active listening.
    *   **Multilingual Support**: Chat in English, Hindi, Spanish, French, and more.
    *   **Smart Context**: Remembers your session context for meaningful conversations.

*   **📊 Smart Dashboard**:
    *   **Emotional Analytics**: Visual charts for mood trends and emotion breakdowns.
    *   **Gamified Wellness**: Daily challenges ("Missions") with XP and streak tracking.
    *   **Personalized Plans**: AI-generated wellness plans based on your current state.

*   **🎨 Futuristic UI/UX**:
    *   **Dynamic Visuals**: interactive 3D ASCII text effects and WebGL backgrounds.
    *   **Glassmorphism Design**: Frosted glass panels, neon accents, and dark mode aesthetics.
    *   **Smooth Animations**: iOS-style transitions and hover effects.
    *   **Responsive**: Fully optimized for desktop and mobile devices.

*   **🔐 Secure & Personal**:
    *   **User Profiles**: Edit your bio, age, and details.
    *   **History**: Save and revisit past conversations.
    *   **Authentication**: Secure Google Sign-In and Anonymous Guest access via Firebase.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask, Waitress (Production Server)
*   **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS
*   **Visuals**: Three.js (WebGL), Custom Canvas Effects
*   **Database & Auth**: Firebase (Firestore, Authentication)
*   **AI Engine**: Google Cloud Vertex AI (Custom Tuned Model)
*   **Containerization**: Docker

## 🚀 Getting Started

Follow these instructions to run the project locally.

### Prerequisites

*   Python 3.8 or higher (or Docker)
*   A Google Cloud Project with **Vertex AI** access
*   A **Firebase Project** (for Auth/Firestore)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/Sankalp-AI.git
    cd Sankalp-AI
    ```

2.  **Environment Setup**
    Create a `.env` file in the root directory:
    ```bash
    GOOGLE_API_KEY=your_gemini_api_key_here
    FIREBASE_API_KEY=your_firebase_api_key
    # ... add other firebase config keys as needed based on server.py context injection
    TUNED_MODEL_NAME=projects/.../locations/.../endpoints/... # Your Vertex AI Endpoint
    ```

### Option A: Running with Docker (Recommended)

1.  **Build the Image**
    ```bash
    docker build -t sankalp-ai .
    ```

2.  **Run the Container**
    ```bash
    docker run -p 8080:8080 --env-file .env sankalp-ai
    ```
    Access at `http://localhost:8080`

### Option B: Running Manually

1.  **Install Python Dependencies**
    ```bash
    # Create venv (Windows)
    python -m venv venv
    .\venv\Scripts\activate

    # Install requirements
    pip install -r requirements.txt
    ```

2.  **Run the Application**
    ```bash
    python server.py
    ```
    *Note: The server runs on `http://0.0.0.0:8080` by default using Waitress.*

3.  **Access the App**
    Open your browser and navigate to: `http://localhost:8080`

## 📂 Project Structure

```
Sankalp-AI/
├── Dockerfile          # Docker Configuration
├── server.py           # Main Flask Application & API Routes
├── requirements.txt    # Python Dependencies
├── .env                # Environment Variables (API Keys)
├── templates/          # HTML Templates (Jinja2)
│   ├── base.html       # Base layout with scripts/styles
│   ├── landing.html    # Marketing Landing Page
│   ├── dashboard.html  # User Dashboard
│   └── chat.html       # Chat Interface
└── static/
    ├── css/
    │   └── style.css   # Main Stylesheet (Glassmorphism theme)
    └── js/
        ├── ascii-text.js # 3D ASCII Text Effect (Three.js)
        ├── main.js     # Firebase Init & Global Logic
        └── visuals.js  # Visual Effects
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to help improve Sankalp.

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

---

*Disclaimer: Sankalp is an AI assistant and not a substitute for professional medical advice. If you are in crisis, please contact local emergency services.*
