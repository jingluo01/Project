from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # 测试数据库连接 - 使用新的SQLAlchemy语法
        with db.engine.connect() as connection:
            result = connection.execute(text('SELECT 1'))
            print("数据库连接成功！")
            print(f"测试查询结果: {result.fetchone()}")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("请检查:")
        print("1. MySQL服务是否启动")
        print("2. 数据库配置是否正确")
        print("3. 数据库 'campus_parking_db' 是否存在")