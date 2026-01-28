# Contributing to Sankalp Chatbot

Thank you for your interest in contributing to Sankalp! We welcome contributions from the community to help make mental health support more accessible to youth.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-username/Sankalp-Chatbot-v1.git
    cd Sankalp-Chatbot-v1
    ```
3.  **Set up the environment**:
    *   Install Python 3.8+.
    *   Create a virtual environment (optional but recommended): `python -m venv venv`
    *   Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows).
    *   Install dependencies: `pip install -r requirements.txt`
4.  **Configure Environment Variables**:
    *   Duplicate `.env.example` to `.env`.
    *   Add your `GOOGLE_API_KEY` (Gemini) and Firebase config.

## Development Workflow

1.  Create a new branch for your feature or fix: `git checkout -b feature/amazing-feature`.
2.  Make your changes.
3.  Test your changes locally by running `python app.py`.
4.  Commit your changes with clear messages.
5.  Push to your fork: `git push origin feature/amazing-feature`.
6.  Open a **Pull Request** to the `main` branch.

## Code Style

*   **Python**: Follow PEP 8 guidelines.
*   **HTML/CSS**: Keep existing structure and class naming consistent.
*   **JavaScript**: Use modern ES6+ syntax.

## Reporting Issues

If you find a bug or have a feature request, please open an issue in the repository with details on how to reproduce it.

Thank you for helping us build a better future!
