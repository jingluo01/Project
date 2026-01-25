from datetime import datetime, timedelta
from app.models.order import ParkingOrder
from app.services.order_service import OrderService

def check_timeout_orders(app):
    """检查超时未支付订单"""
    with app.app_context():
        timeout_hours = app.config['PAYMENT_TIMEOUT_HOURS']
        
        # 查找待支付且超过24小时的订单
        timeout_threshold = datetime.utcnow() - timedelta(hours=timeout_hours)
        
        timeout_orders = ParkingOrder.query.filter(
            ParkingOrder.status == 2,  # 待支付
            ParkingOrder.out_time < timeout_threshold
        ).all()
        
        for order in timeout_orders:
            # 调用 Service 层统一处理违约 (支付超时)
            result, _ = OrderService.process_order_violation(order.order_id, violation_type='payment')
            if result['success']:
                print(result['message'])
            else:
                print(f"执行支付超时处理失败: {result['message']}")

def check_reservation_timeout(app):
    """检查预约超时未入场订单"""
    with app.app_context():
        timeout_minutes = app.config.get('RESERVATION_TIMEOUT_MINUTES', 30)
        
        # 查找已预约且超过30分钟未入场的订单
        threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        timeout_reservations = ParkingOrder.query.filter(
            ParkingOrder.status == 0, # 已预约
            ParkingOrder.reserve_time < threshold
        ).all()
        
        for order in timeout_reservations:
            # 调用 Service 层统一处理违约 (预约超时)
            result, _ = OrderService.process_order_violation(order.order_id, violation_type='reservation')
            if result['success']:
                print(result['message'])
            else:
                print(f"执行预约超时处理失败: {result['message']}")

def start_scheduler(app):
    """启动定时任务 (增加了防止重复启动的检查)"""
    import os
    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return

    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    
    # 待支付超时检查 (加速测试，每分钟检查一次)
    scheduler.add_job(
        func=lambda: check_timeout_orders(app),
        trigger='interval',
        minutes=1,
        id='check_payment_timeout'
    )
    
    # 预约超时检查 (每分钟)
    scheduler.add_job(
        func=lambda: check_reservation_timeout(app),
        trigger='interval',
        minutes=1,
        id='check_reservation_timeout'
    )
    
    scheduler.start()
    print('定时任务已启动 (测试模式: 1分钟频率，已接入 Service 指挥)')
