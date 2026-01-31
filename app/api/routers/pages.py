from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    return render_template('landing.html')

@pages_bp.route('/chat')
def chat():
    return render_template('chat.html')

@pages_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
