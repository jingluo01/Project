from datetime import datetime
from decimal import Decimal

def calculate_parking_fee(in_time, out_time, fee_rate, free_time_minutes, user_role, role_discount):
    """
    计算停车费用
    
    Args:
        in_time: 入场时间
        out_time: 出场时间
        fee_rate: 每小时费率
        free_time_minutes: 免费时长(分钟)
        user_role: 用户角色
        role_discount: 角色折扣配置
    
    Returns:
        Decimal: 应付费用
    """
    import math
    from app.models.config import SysConfig
    import json

    if not in_time or not out_time:
        return Decimal('0.00')
    
    # 计算停车时长(分钟)
    duration = (out_time - in_time).total_seconds() / 60
    
    # --- 核心：免费时长逻辑 ---
    # 测试模式：暂时注释掉免费时长判断，确保每次都能产生费用测试支付
    # if duration <= free_time_minutes:
    #     return Decimal('0.00')
    
    # 计费规则：超过免费时长后，按小时计费，不足1小时按1小时计 (向上取整)
    chargeable_hours = math.ceil(duration / 60)
    
    # 1. 获取动态业务配置
    # 获取倍率因子 (默认 1.0)
    db_multiplier = SysConfig.get_value('FEE_MULTIPLIER', '1.0')
    multiplier = Decimal(str(db_multiplier))
    
    # 2. 获取动态角色折扣 (默认无折扣)
    db_discounts = SysConfig.get_value('ROLE_DISCOUNT')
    if db_discounts:
        try:
            discounts = json.loads(db_discounts)
            discount_val = discounts.get(str(user_role), 1.0)
        except:
            discount_val = 1.0
    else:
        # 兼容旧配置
        discount_val = role_discount.get(user_role, 1.0)
        
    discount = Decimal(str(discount_val))
    
    # 3. 计算最终费用
    final_fee = Decimal(str(chargeable_hours)) * Decimal(str(fee_rate)) * discount * multiplier
    
    # 保留两位小数
    return final_fee.quantize(Decimal('0.01'))

def get_discount_rate(user_role, role_discount):
    """获取用户折扣率"""
    return role_discount.get(user_role, 1.0)
