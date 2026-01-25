from sqlalchemy import func, and_
from datetime import datetime, timedelta
from decimal import Decimal
from app.extensions import db
from app.models.order import ParkingOrder
from app.models.parking import ParkingSpot

class AdminService:
    @staticmethod
    def get_stats():
        """获取仪表盘统计数据逻辑 (纯后台聚合逻辑)"""
        today = datetime.utcnow().date()
        
        today_revenue = db.session.query(func.sum(ParkingOrder.total_fee)).filter(
            and_(
                ParkingOrder.status == 3,
                func.date(ParkingOrder.pay_time) == today
            )
        ).scalar() or Decimal('0.00')
        
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
                'active_users': active_users,
                'current_orders': current_orders,
                'available_spots': available_spots,
                'revenue_trend': revenue_trend,
                'utilization_rate': round(utilization_rate, 2)
            }
        }, 200
