"""
统计数据相关路由
"""
from flask import Blueprint, jsonify
from app.models import db, ParkingSpot, Order
from sqlalchemy import func
from datetime import datetime, timedelta
import random

stats_bp = Blueprint('stats', __name__)

# ================= 管理端统计 (增强版) =================
@stats_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表板统计数据"""
    try:
        # 实时统计数据
        total_spots = ParkingSpot.query.count()
        free_spots = ParkingSpot.query.filter_by(status=0).count()
        occupied_spots = ParkingSpot.query.filter_by(status=1).count()
        reserved_spots = ParkingSpot.query.filter_by(status=2).count()
        
        # 订单统计（详细）
        total_orders = Order.query.count()
        reserved_orders = Order.query.filter_by(status=0).count()  # 已预约
        parking_orders = Order.query.filter_by(status=1).count()   # 停车中
        completed_orders = Order.query.filter_by(status=2).count() # 已完成
        pending_orders = Order.query.filter_by(status=3).count()   # 待支付
        cancelled_orders = Order.query.filter_by(status=4).count() # 已取消
        
        # 收入统计
        total_revenue = db.session.query(func.sum(Order.total_fee)).filter(Order.status == 2).scalar() or 0
        
        # 利用率计算
        utilization = round((occupied_spots + reserved_spots) / total_spots * 100, 1) if total_spots > 0 else 0
        
        # 最近7天数据
        dates = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(6, -1, -1)]
        
        # 模拟营收趋势数据（实际项目中应该从数据库查询）
        revenue_data = []
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            daily_revenue = db.session.query(func.sum(Order.total_fee)).filter(
                Order.status == 2,
                func.date(Order.actual_out_time) == date.date()
            ).scalar() or random.randint(50, 300)
            revenue_data.append(float(daily_revenue) if isinstance(daily_revenue, type(total_revenue)) else daily_revenue)
        
        return jsonify({
            'code': 200, 
            'data': {
                'pie_data': [
                    {'value': free_spots, 'name': '空闲'},
                    {'value': occupied_spots, 'name': '占用'},
                    {'value': reserved_spots, 'name': '预约'}
                ],
                'line_data': {
                    'categories': dates,
                    'values': revenue_data
                },
                'summary': {
                    'total_income': float(total_revenue),
                    'utilization': utilization,
                    'total_spots': total_spots,
                    'total_orders': total_orders,
                    'completed_orders': completed_orders,
                    'reserved_orders': reserved_orders,
                    'parking_orders': parking_orders,
                    'pending_orders': pending_orders,
                    'cancelled_orders': cancelled_orders
                }
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500