import re

def validate_plate_number(plate_number):
    """
    验证车牌号格式
    支持: 京A88888, 京A8888学, 沪B12345, 粤B12345D等
    """
    if not plate_number:
        return False
    
    # 简化的车牌号验证规则
    pattern = r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4,5}[A-Z0-9挂学警港澳]?$'
    return bool(re.match(pattern, plate_number))

def validate_user_no(user_no):
    """
    验证学号/工号格式
    支持: 字母数字组合,4-20位
    """
    if not user_no:
        return False
    
    pattern = r'^[A-Za-z0-9]{4,20}$'
    return bool(re.match(pattern, user_no))

def validate_phone(phone):
    """验证手机号格式"""
    if not phone:
        return False
    
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))
