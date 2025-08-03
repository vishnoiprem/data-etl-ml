"""
Web application for the Agentic AI System
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import asyncio
import uuid
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agentic_engine import AgenticAIEngine
from utils.config import load_config
from utils.logging_config import setup_logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize logging
setup_logging()

# Load configuration
config = load_config()

# Initialize the Agentic AI Engine
agentic_engine = AgenticAIEngine(config)


@app.route('/')
def index():
    """Main interface"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Analytics dashboard"""
    metrics = agentic_engine.get_metrics()
    return render_template('dashboard.html', metrics=metrics)


@app.route('/api/metrics')
def get_metrics():
    """API endpoint for metrics"""
    return jsonify(agentic_engine.get_metrics())


@socketio.on('user_message')
def handle_user_message(data):
    """Handle real-time user messages"""
    user_message = data.get('message', '')
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id

    # Emit processing status
    emit('agent_status', {'status': 'processing', 'step': 'perceive'})

    # Process the message asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            agentic_engine.process_request(user_message, session_id)
        )

        # Send the response back
        emit('agent_response', {
            'success': result['success'],
            'response': result.get('response', ''),
            'confidence': result.get('confidence', 0),
            'processing_time': result.get('processing_time', 0),
            'actions_taken': result.get('actions_taken', [])
        })

    except Exception as e:
        emit('agent_response', {
            'success': False,
            'error': str(e),
            'response': 'I encountered an error processing your request.'
        })
    finally:
        loop.close()


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    emit('connected', {'session_id': session_id})


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)