from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # 使用稳定的配置运行应用
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5001, 
        debug=False,
        use_reloader=False,
        log_output=False,
        allow_unsafe_werkzeug=True
    )