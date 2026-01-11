from app import create_app, db
from app.models import User, Car, ParkingSpot, Order

app = create_app()

with app.app_context():
    try:
        print("开始测试数据库表...")
        
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建成功！")
        
        # 测试表是否存在 - 使用新的SQLAlchemy语法
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        expected_tables = ['sys_user', 'car', 'parking_spot', 'parking_order']
        
        print("\n检查表是否存在:")
        for table in expected_tables:
            if table in tables:
                print(f"✓ 表 '{table}' 存在")
            else:
                print(f"✗ 表 '{table}' 不存在")
        
        print(f"\n数据库中所有表: {tables}")
        
    except Exception as e:
        print(f"数据库表测试失败: {e}")