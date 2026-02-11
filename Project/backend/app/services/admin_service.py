from sqlalchemy import func, and_
from datetime import datetime, timedelta
from decimal import Decimal
import json
from app.extensions import db
from app.models.order import ParkingOrder
from app.models.parking import ParkingSpot
from app.models.config import SysConfig

class AdminService:
    @staticmethod
    def get_stats():
        """获取仪表盘统计数据逻辑 (增加动态增长率计算)"""
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        today_revenue = db.session.query(func.sum(ParkingOrder.total_fee)).filter(
            and_(
                ParkingOrder.status == 3,
                func.date(ParkingOrder.pay_time) == today
            )
        ).scalar() or Decimal('0.00')

        yesterday_revenue = db.session.query(func.sum(ParkingOrder.total_fee)).filter(
            and_(
                ParkingOrder.status == 3,
                func.date(ParkingOrder.pay_time) == yesterday
            )
        ).scalar() or Decimal('0.00')
        
        # 计算增长率
        growth = 0
        if yesterday_revenue > 0:
            growth = round(float((today_revenue - yesterday_revenue) / yesterday_revenue * 100), 1)
        elif today_revenue > 0:
            growth = 100.0
            
        active_users = db.session.query(func.count(func.distinct(ParkingOrder.user_id))).filter(
            ParkingOrder.status == 1
        ).scalar() or 0
        
        current_orders = ParkingOrder.query.filter(
            ParkingOrder.status.in_([0, 1])
        ).count()
        
        available_spots = ParkingSpot.query.filter_by(status=0).count()
        
        revenue_trend = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            daily_revenue = db.session.query(func.sum(ParkingOrder.total_fee)).filter(
                and_(
                    ParkingOrder.status == 3,
                    func.date(ParkingOrder.pay_time) == date
                )
            ).scalar() or Decimal('0.00')
            revenue_trend.append({
                'date': date.isoformat(),
                'revenue': float(daily_revenue)
            })
        
        total_spots = ParkingSpot.query.count()
        occupied_spots = ParkingSpot.query.filter(ParkingSpot.status.in_([1, 2])).count()
        utilization_rate = (occupied_spots / total_spots * 100) if total_spots > 0 else 0
        
        return {
            'success': True,
            'data': {
                'today_revenue': float(today_revenue),
                'revenue_growth': growth,
                'active_users': active_users,
                'current_orders': current_orders,
                'available_spots': available_spots,
                'revenue_trend': revenue_trend,
                'utilization_rate': round(utilization_rate, 2)
            }
        }, 200

    @staticmethod
    def get_system_config():
        """获取系统配置 (数据库优先)"""
        from flask import current_app
        app_config = current_app.config
        
        # 尝试从数据库读取，若无则使用代码配置并初始化数据库
        def fetch_config(key, default_val):
            db_val = SysConfig.get_value(key)
            if db_val is not None:
                # 尝试解析 JSON (针对 roles 等复杂结构)
                try:
                    return json.loads(db_val)
                except:
                    # 尝试转换数字类型
                    try:
                        if '.' in db_val: return float(db_val)
                        return int(db_val)
                    except:
                        return db_val
            else:
                # 初始化数据库
                val_to_store = json.dumps(default_val) if isinstance(default_val, (dict, list)) else str(default_val)
                SysConfig.set_value(key, val_to_store)
                return default_val

        data = {
            'credit_thresholds': {
                'min': fetch_config('MIN_CREDIT_SCORE', app_config.get('MIN_CREDIT_SCORE', 70)),
                'perfect': fetch_config('PERFECT_CREDIT_SCORE', app_config.get('PERFECT_CREDIT_SCORE', 100)),
                'good': fetch_config('GOOD_CREDIT_SCORE', app_config.get('GOOD_CREDIT_SCORE', 85)),
            },
            'roles': fetch_config('ROLE_DISCOUNT', app_config.get('ROLE_DISCOUNT', {})),
            'violation_fee': fetch_config('VIOLATION_FEE', app_config.get('VIOLATION_FEE', 5.0)),
            'reservation_timeout': fetch_config('RESERVATION_TIMEOUT_MINUTES', app_config.get('RESERVATION_TIMEOUT_MINUTES', 30)),
            'fee_multiplier': fetch_config('FEE_MULTIPLIER', app_config.get('FEE_MULTIPLIER', 10.0)),
            'payment_timeout': fetch_config('PAYMENT_TIMEOUT_HOURS', app_config.get('PAYMENT_TIMEOUT_HOURS', 24)),
            'penalty_timeout': fetch_config('CREDIT_PENALTY_TIMEOUT', app_config.get('CREDIT_PENALTY_TIMEOUT', 30)),
            'penalty_delay': fetch_config('CREDIT_PENALTY_DELAY', app_config.get('CREDIT_PENALTY_DELAY', 10))
        }
        return {'success': True, 'data': data}, 200

    @staticmethod
    def update_system_config(data):
        """批量更新系统配置至数据库"""
        try:
            if 'credit_thresholds' in data:
                c = data['credit_thresholds']
                if 'min' in c: SysConfig.set_value('MIN_CREDIT_SCORE', c['min'])
                if 'good' in c: SysConfig.set_value('GOOD_CREDIT_SCORE', c['good'])
                if 'perfect' in c: SysConfig.set_value('PERFECT_CREDIT_SCORE', c['perfect'])
            
            if 'roles' in data:
                SysConfig.set_value('ROLE_DISCOUNT', json.dumps(data['roles']))
            
            if 'violation_fee' in data:
                SysConfig.set_value('VIOLATION_FEE', data['violation_fee'])
            
            if 'reservation_timeout' in data:
                SysConfig.set_value('RESERVATION_TIMEOUT_MINUTES', data['reservation_timeout'])
            
            if 'fee_multiplier' in data:
                SysConfig.set_value('FEE_MULTIPLIER', data['fee_multiplier'])
            
            if 'payment_timeout' in data:
                SysConfig.set_value('PAYMENT_TIMEOUT_HOURS', data['payment_timeout'])

            if 'penalty_timeout' in data:
                SysConfig.set_value('CREDIT_PENALTY_TIMEOUT', data['penalty_timeout'])
            
            if 'penalty_delay' in data:
                SysConfig.set_value('CREDIT_PENALTY_DELAY', data['penalty_delay'])
                
            return {'success': True, 'message': '配置更新成功，已实时生效'}, 200
        except Exception as e:
            return {'success': False, 'message': f'更新失败: {str(e)}'}, 500
