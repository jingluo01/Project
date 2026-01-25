import os
import sys
from app import create_app
from app.extensions import db
from app.models.user import SysUser
from app.models.car import Car
from app.models.parking import ParkingZone, ParkingSpot
from app.models.order import ParkingOrder
from app.utils.auth_utils import hash_password

def init_database():
    """初始化数据库"""
    app = create_app('development')
    
    with app.app_context():
        # 创建所有表
        print('Creating database tables...')
        db.create_all()
        
        # 检查是否已有数据
        if SysUser.query.first():
            print('Database already initialized.')
            return
        
        print('Initializing seed data...')
        
        # 创建管理员账户
        admin = SysUser(
            user_no='admin',
            username='系统管理员',
            password=hash_password('admin123'),
            role=3,  # 管理员
            balance=10000.00,
            credit_score=100
        )
        db.session.add(admin)
        
        # 创建测试学生用户
        student = SysUser(
            user_no='2021001',
            username='李同学',
            password=hash_password('123456'),
            role=1,  # 学生
            balance=156.00,
            credit_score=98
        )
        db.session.add(student)
        
        # 创建测试教师用户
        teacher = SysUser(
            user_no='T2021001',
            username='王老师',
            password=hash_password('123456'),
            role=2,  # 教职工
            balance=500.00,
            credit_score=100
        )
        db.session.add(teacher)
        
        # 创建外部用户(用于临时访客)
        guest = SysUser(
            user_no='guest',
            username='访客用户',
            password=hash_password('guest123'),
            role=0,  # 外部用户
            balance=0.00,
            credit_score=100
        )
        db.session.add(guest)
        
        db.session.commit()
        
        # 为学生绑定车辆
        car1 = Car(user_id=student.user_id, plate_number='京A88888')
        car2 = Car(user_id=teacher.user_id, plate_number='京B12345')
        db.session.add_all([car1, car2])
        
        # 创建停车区域
        zone_a = ParkingZone(
            zone_name='A区(教学楼)',
            fee_rate=5.00,
            free_time=15
        )
        zone_b = ParkingZone(
            zone_name='B区(宿舍)',
            fee_rate=3.00,
            free_time=30
        )
        zone_c = ParkingZone(
            zone_name='C区(访客)',
            fee_rate=10.00,
            free_time=10
        )
        db.session.add_all([zone_a, zone_b, zone_c])
        db.session.commit()
        
        # 创建车位
        spots = []
        for zone in [zone_a, zone_b, zone_c]:
            zone_prefix = zone.zone_name[0]  # A, B, C
            for i in range(1, 16):  # 每个区域15个车位
                spot = ParkingSpot(
                    spot_no=f'{zone_prefix}-{i:03d}',
                    zone_id=zone.zone_id,
                    status=0  # 空闲
                )
                spots.append(spot)
        
        db.session.add_all(spots)
        db.session.commit()
        
        print(f'Created {len(spots)} parking spots')
        print('Database initialized successfully!')
        print('\nTest accounts:')
        print('Admin: admin / admin123')
        print('Student: 2021001 / 123456')
        print('Teacher: T2021001 / 123456')

if __name__ == '__main__':
    init_database()
