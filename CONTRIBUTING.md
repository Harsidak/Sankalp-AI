# Contributing to Sankalp

Thank you for your interest in contributing to Sankalp! We welcome contributions from the community to help make mental health support more accessible to youth.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/Harsidak/Sankalp-AI.git
    cd Sankalp-AI
    ```
3.  **Set up the environment**:
    *   **Option A: Virtual Environment**
        *   Install Python 3.12+.
        *   Create venv: `python -m venv venv`
        *   Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows).
        *   Install dependencies: `pip install -r requirements.txt`
        *   Run server: `python server.py`
    *   **Option B: Docker**
        *   Build: `docker build -t sankalp .`
        *   Run: `docker run -p 8080:8080 --env-file .env sankalp`

4.  **Configure Environment Variables**:
    *   Create a `.env` file in the root.
    *   Add at least `GOOGLE_API_KEY` (Gemini) and `FIREBASE_*` config keys.

## Development Workflow

1.  Create a new branch for your feature or fix: `git checkout -b feature/amazing-feature`.
2.  Make your changes.
3.  Test your changes locally at `http://localhost:8080`.
4.  Commit your changes with clear messages.
5.  Push to your fork: `git push origin feature/amazing-feature`.
6.  Open a **Pull Request** to the `main` branch.

## Code Style

*   **Python**: Follow PEP 8 guidelines.
*   **HTML/Templates**: Use Jinja2 formatting.
*   **JavaScript**: Use modern ES6+ syntax. Avoid inline styles where possible (use Tailwind).
*   **Commits**: Use clear, descriptive commit messages.

## Reporting Issues

If you find a bug or have a feature request, please open an issue in the repository with details on how to reproduce it.

Thank you for helping us build a better future!
