# Sankalp: AI Mental Health Companion

![Sankalp Banner](https://via.placeholder.com/1200x400/1a1a2e/7F5AF0?text=Sankalp+AI+Companion)

**Sankalp** is a compassionate, AI-powered mental health assistant designed specifically for students and youth. It provides a safe, non-judgmental space to express feelings, track emotional well-being, and build resilience through gamified challenges.

Built with a futuristic "Frosty Glass" UI, Sankalp combines advanced psychology with cutting-edge AI (Google Gemini) to offer real-time support in multiple languages.

## ✨ Key Features

*   **🤖 Empathetic AI Chat**:
    *   Powered by a **Custom Fine-Tuned Model on Vertex AI**.
    *   Specialized training on psychological frameworks and youth mental health datasets.
    *   Provides validation, coping strategies, and active listening.
    *   Supports speech-to-text input for hands-free interaction.
    *   Context-aware conversations (remembers your session context).

*   **📊 Smart Dashboard**:
    *   **Emotional Analytics**: Visual charts for mood trends and emotion breakdowns.
    *   **Gamified Wellness**: Daily challenges ("Missions") with XP and streak tracking.
    *   **Personalized Plans**: AI-generated wellness plans based on your current state.

*   **🎨 Futuristic UI/UX**:
    *   **Glassmorphism Design**: Frosted glass panels, neon accents, and dark mode aesthetics.
    *   **Smooth Animations**: iOS-style transitions and hover effects.
    *   **Responsive**: Fully optimized for desktop and mobile devices.

*   **🔐 Secure & Personal**:
    *   **User Profiles**: Edit your bio, age, and details.
    *   **History**: Save and revisit past conversations.
    *   **Authentication**: Secure Google Sign-In and Anonymous Guest access via Firebase.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask
*   **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS
*   **Styling**: Custom CSS (Glassmorphism, Animations)
*   **Database & Auth**: Firebase (Firestore, Authentication)
*   **AI Engine**: Google Generative AI (Gemini)

## 🚀 Getting Started

Follow these instructions to run the project locally.

### Prerequisites

*   Python 3.8 or higher
*   A Google Cloud Project with **Gemini API** access
*   A **Firebase Project** (for Auth/Firestore)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/Sankalp-Chatbot-v1.git
    cd Sankalp-Chatbot-v1
    ```

2.  **Install Python Dependencies**
    It is recommended to use a virtual environment.
    ```bash
    # Create venv (Windows)
    python -m venv venv
    .\venv\Scripts\activate

    # Install requirements
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**
    Create a `.env` file in the root directory:
    ```bash
    GOOGLE_API_KEY=your_actual_gemini_api_key_here
    ```

4.  **Configure Firebase**
    *   Update `static/js/main.js` with your Firebase Config object (replace the existing placeholder config if needed).
    *   Ensure Firestore Database and Authentication (Google/Anonymous) are enabled in your Firebase Console.

5.  **Run the Application**
    ```bash
    python app.py
    ```

6.  **Access the App**
    Open your browser and navigate to: `http://localhost:8080`

## 📂 Project Structure

```
Sankalp-Chatbot-v1/
├── app.py              # Main Flask Application & API Routes
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
        └── main.js     # Firebase Init & Global Logic
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to help improve Sankalp.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Disclaimer: Sankalp is an AI assistant and not a substitute for professional medical advice. If you are in crisis, please contact local emergency services.*
