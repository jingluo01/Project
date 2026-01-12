"""
停车费用计算服务（适配现有数据库结构）
"""
from datetime import datetime
from decimal import Decimal
from app.models import db, FeeRule, User, ParkingSpot, Order
import math


class FeeCalculationService:
    """费用计算服务"""
    
    @staticmethod
    def calculate_parking_fee(user_id: int, spot_id: int, duration_minutes: int, 
                            parking_time: datetime = None) -> dict:
        """
        计算停车费用
        
        Args:
            user_id: 用户ID
            spot_id: 车位ID
            duration_minutes: 停车时长（分钟）
            parking_time: 停车时间（用于时间段规则）
            
        Returns:
            dict: 包含费用信息的字典
        """
        if parking_time is None:
            parking_time = datetime.now()
            
        # 获取用户信息
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
            
        # 获取适用的费用规则
        applicable_rule = FeeCalculationService._get_applicable_rule(user.role)
        
        if not applicable_rule:
            # 如果没有找到规则，使用默认规则
            applicable_rule = FeeCalculationService._get_default_rule()
            
        # 计算费用
        fee_info = FeeCalculationService._calculate_fee_by_rule(
            applicable_rule, duration_minutes
        )
        
        # 添加规则信息
        fee_info['applied_rule'] = applicable_rule.to_dict() if applicable_rule else None
        fee_info['user_role'] = user.role
        
        return fee_info
    
    @staticmethod
    def _get_applicable_rule(user_role: str) -> FeeRule:
        """
        获取适用的费用规则（简化版）
        """
        # 查找匹配用户角色的规则
        rule = FeeRule.query.filter(FeeRule.target_role == user_role).first()
        return rule
    
    @staticmethod
    def _get_default_rule() -> FeeRule:
        """获取默认规则"""
        # 创建一个临时的默认规则对象
        default_rule = FeeRule()
        default_rule.rule_name = '默认规则'
        default_rule.target_role = 'default'
        default_rule.base_price = Decimal('2.00')
        default_rule.unit_price = Decimal('0.1')
        default_rule.free_minutes = 15
        return default_rule
    
    @staticmethod
    def _calculate_fee_by_rule(rule: FeeRule, duration_minutes: int) -> dict:
        """
        根据规则计算费用（简化版）
        
        Args:
            rule: 费用规则
            duration_minutes: 停车时长（分钟）
            
        Returns:
            dict: 费用计算结果
        """
        # 免费时长处理
        if duration_minutes <= rule.free_minutes:
            return {
                'total_fee': 0.00,
                'base_fee': 0.00,
                'time_fee': 0.00,
                'duration_minutes': duration_minutes,
                'free_minutes_used': duration_minutes,
                'billable_minutes': 0,
                'calculation_method': 'free_period'
            }
        
        # 计算需要收费的时长
        billable_minutes = duration_minutes - rule.free_minutes
        
        # 基础费用
        base_fee = float(rule.base_price)
        
        # 时间费用计算（改为按小时计费）
        # 将分钟转换为小时，向上取整
        billable_hours = (billable_minutes + 59) // 60  # 向上取整到小时
        
        # 每小时费率（假设unit_price存储的是每小时费率）
        hourly_rate = 2.0  # 每小时2元
        time_fee = hourly_rate * billable_hours
        
        # 总费用
        total_fee = base_fee + time_fee
        
        return {
            'total_fee': round(total_fee, 2),
            'base_fee': base_fee,
            'time_fee': round(time_fee, 2),
            'duration_minutes': duration_minutes,
            'free_minutes_used': rule.free_minutes,
            'billable_minutes': billable_minutes,
            'billable_hours': billable_hours,
            'calculation_method': 'base_plus_hourly_rate',
            'rate_applied': {
                'per_hour': hourly_rate,
                'per_hour': None
            }
        }
    
    @staticmethod
    def get_daily_fee_total(user_id: int, date: datetime = None) -> float:
        """
        获取用户当日已产生的停车费用总额
        
        Args:
            user_id: 用户ID
            date: 日期（默认今天）
            
        Returns:
            float: 当日费用总额
        """
        if date is None:
            date = datetime.now()
            
        # 查询当日已完成的订单
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        total = db.session.query(db.func.sum(Order.total_fee)).filter(
            Order.user_id == user_id,
            Order.status == 2,  # 已完成
            Order.actual_out_time >= start_of_day,
            Order.actual_out_time <= end_of_day
        ).scalar()
        
        return float(total) if total else 0.0


class FeeRuleManagementService:
    """费用规则管理服务（简化版）"""
    
    @staticmethod
    def create_rule(rule_data: dict) -> FeeRule:
        """创建费用规则"""
        # 映射字段名
        mapped_data = {
            'rule_name': rule_data.get('rule_name', '新规则'),
            'target_role': rule_data.get('user_role', rule_data.get('target_role')),
            'base_price': Decimal(str(rule_data.get('base_fee', 0))),
            'unit_price': Decimal(str(rule_data.get('rate_per_minute', 0))),
            'free_minutes': rule_data.get('free_minutes', 0)
        }
        
        rule = FeeRule(**mapped_data)
        db.session.add(rule)
        db.session.commit()
        return rule
    
    @staticmethod
    def update_rule(rule_id: int, rule_data: dict) -> FeeRule:
        """更新费用规则"""
        rule = db.session.get(FeeRule, rule_id)
        if not rule:
            raise ValueError("规则不存在")
            
        # 映射字段名并更新
        if 'rule_name' in rule_data:
            rule.rule_name = rule_data['rule_name']
        if 'user_role' in rule_data or 'target_role' in rule_data:
            rule.target_role = rule_data.get('user_role', rule_data.get('target_role'))
        if 'base_fee' in rule_data:
            rule.base_price = Decimal(str(rule_data['base_fee']))
        if 'rate_per_minute' in rule_data:
            rule.unit_price = Decimal(str(rule_data['rate_per_minute']))
        if 'free_minutes' in rule_data:
            rule.free_minutes = rule_data['free_minutes']
                
        db.session.commit()
        return rule
    
    @staticmethod
    def delete_rule(rule_id: int) -> bool:
        """删除费用规则"""
        rule = db.session.get(FeeRule, rule_id)
        if not rule:
            return False
            
        db.session.delete(rule)
        db.session.commit()
        return True
    
    @staticmethod
    def get_rules_by_role(user_role: str = None) -> list:
        """获取指定角色的费用规则"""
        query = FeeRule.query
        if user_role:
            query = query.filter(FeeRule.target_role == user_role)
            
        return query.order_by(FeeRule.rule_id.desc()).all()
    
    @staticmethod
    def initialize_default_rules():
        """初始化默认费用规则（检查现有数据）"""
        # 检查是否已有规则
        existing_rules = FeeRule.query.count()
        if existing_rules > 0:
            print(f"已存在 {existing_rules} 条费用规则，跳过初始化")
            return
            
        default_rules = [
            {
                'rule_name': '学生标准',
                'target_role': 'student',
                'base_price': Decimal('1.00'),
                'unit_price': Decimal('0.05'),
                'free_minutes': 30
            },
            {
                'rule_name': '教师优惠',
                'target_role': 'teacher',
                'base_price': Decimal('0.50'),
                'unit_price': Decimal('0.03'),
                'free_minutes': 60
            },
            {
                'rule_name': '管理员免费',
                'target_role': 'admin',
                'base_price': Decimal('0.00'),
                'unit_price': Decimal('0.00'),
                'free_minutes': 999999
            },
            {
                'rule_name': '访客标准',
                'target_role': 'visitor',
                'base_price': Decimal('3.00'),
                'unit_price': Decimal('0.15'),
                'free_minutes': 0
            }
        ]
        
        for rule_data in default_rules:
            rule = FeeRule(**rule_data)
            db.session.add(rule)
        
        db.session.commit()
        print(f"初始化了 {len(default_rules)} 条默认费用规则")