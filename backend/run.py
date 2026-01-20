import os
from app import create_app, socketio

# 从环境变量获取配置模式，默认为 'default'
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # 注意：使用 socketio.run 而不是 app.run，以支持 WebSocket
    # 使用端口 5001 避免与 macOS AirPlay 冲突
    print("🚀 Smart Parking System is starting on http://0.0.0.0:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)