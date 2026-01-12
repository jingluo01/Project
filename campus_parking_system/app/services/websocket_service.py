"""
WebSocket 事件服务
"""
from datetime import datetime
from app import socketio
from app.models import db, ParkingSpot, Order, User
from sqlalchemy import func


class WebSocketEventService:
    """WebSocket事件服务"""
    
    @staticmethod
    def emit_data_update(event_type: str, data=None):
        """向所有连接的客户端发送数据更新事件"""
        try:
            socketio.emit('data_update', {
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
        except Exception as e:
            print(f"WebSocket emit error: {e}")

    @staticmethod
    def emit_spot_update():
        """发送车位状态更新"""
        try:
            spots = ParkingSpot.query.all()
            spots_data = []
            for spot in spots:
                spot_info = {
                    'id': spot.spot_id, 
                    'no': spot.spot_no, 
                    'status': spot.status, 
                    'area': spot.area_code,
                    'current_plate': None, 
                    'current_order': None
                }
                if spot.status != 0:
                    active_order = Order.query.filter(
                        Order.spot_id == spot.spot_id, 
                        Order.status.in_([0, 1, 3])
                    ).first()
                    if active_order:
                        spot_info['current_plate'] = active_order.plate_number
                        spot_info['current_order'] = active_order.order_no
                        if active_order.status == 3: 
                            spot_info['status'] = 3
                spots_data.append(spot_info)
            
            WebSocketEventService.emit_data_update('spots_update', spots_data)
        except Exception as e:
            print(f"Spot update error: {e}")

    @staticmethod
    def emit_order_update():
        """发送订单更新"""
        try:
            orders = Order.query.order_by(Order.order_id.desc()).all()
            orders_data = []
            for o in orders:
                u = db.session.get(User, o.user_id)
                orders_data.append({
                    'order_no': o.order_no, 
                    'username': u.real_name if u else "未知", 
                    'plate': o.plate_number,
                    'status': o.status, 
                    'reserve_time': str(o.reserve_start_time) if o.reserve_start_time else '-',
                    'in_time': str(o.actual_in_time) if o.actual_in_time else '-', 
                    'out_time': str(o.actual_out_time) if o.actual_out_time else '-',
                    'fee': str(o.total_fee)
                })
            
            WebSocketEventService.emit_data_update('orders_update', orders_data)
        except Exception as e:
            print(f"Order update error: {e}")

    @staticmethod
    def emit_stats_update():
        """发送统计数据更新"""
        try:
            from datetime import datetime, timedelta
            
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
            
            # 营收趋势数据（从数据库查询实际数据）
            revenue_data = []
            for i in range(7):
                date = datetime.now() - timedelta(days=6-i)
                daily_revenue = db.session.query(func.sum(Order.total_fee)).filter(
                    Order.status == 2,
                    func.date(Order.actual_out_time) == date.date()
                ).scalar()
                # 如果没有数据，使用0而不是随机数
                revenue_data.append(float(daily_revenue) if daily_revenue else 0.0)
            
            stats_data = {
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
            
            print(f"发送统计数据更新")
            WebSocketEventService.emit_data_update('stats_update', stats_data)
        except Exception as e:
            print(f"Stats update error: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def emit_user_notification(user_id: int, message: str, notification_type: str = 'info'):
        """向特定用户发送通知"""
        try:
            socketio.emit('user_notification', {
                'user_id': user_id,
                'message': message,
                'type': notification_type,
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
        except Exception as e:
            print(f"User notification error: {e}")

    @staticmethod
    def emit_system_notification(message: str, notification_type: str = 'info'):
        """发送系统通知"""
        try:
            socketio.emit('system_notification', {
                'message': message,
                'type': notification_type,
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
        except Exception as e:
            print(f"System notification error: {e}")


def register_websocket_handlers():
    """注册 WebSocket 事件处理器"""
    from app import socketio
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接时发送初始数据"""
        print('WebSocket客户端已连接')
        # 发送初始数据
        WebSocketEventService.emit_spot_update()
        WebSocketEventService.emit_order_update()
        WebSocketEventService.emit_stats_update()

    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接"""
        print('WebSocket客户端已断开')

    @socketio.on('request_data')
    def handle_request_data(data):
        """客户端请求特定数据"""
        data_type = data.get('type')
        if data_type == 'spots':
            WebSocketEventService.emit_spot_update()
        elif data_type == 'orders':
            WebSocketEventService.emit_order_update()
        elif data_type == 'stats':
            WebSocketEventService.emit_stats_update()
        elif data_type == 'all':
            WebSocketEventService.emit_spot_update()
            WebSocketEventService.emit_order_update()
            WebSocketEventService.emit_stats_update()