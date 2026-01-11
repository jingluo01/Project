from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True 方便调试，代码修改后自动重启
    app.run(host='0.0.0.0', port=5001, debug=True)