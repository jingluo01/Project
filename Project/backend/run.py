import os
from app import create_app
from app.extensions import socketio
from app.tasks.timeout_checker import start_scheduler

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Start background scheduler
start_scheduler(app)

if __name__ == '__main__':
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
