from flask import Blueprint, jsonify, request
from app.models import User, Car, db # 确保引入了 Car 模型

auth_bp = Blueprint('auth', __name__)

# ================= 1. 登录接口 =================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'code': 400, 'msg': '请输入账号和密码'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return jsonify({'code': 401, 'msg': '账号或密码错误'}), 401
    
    # 登录时顺便查一下车牌
    cars = Car.query.filter_by(user_id=user.user_id).all()
    plate_list = [c.plate_number for c in cars]
    
    return jsonify({
        'code': 200, 'msg': '登录成功',
        'data': {
            'id': user.user_id, 'username': user.username, 'real_name': user.real_name,
            'role': user.role, 'credit': user.credit_score, 'balance': user.balance,
            'plates': plate_list # 返回车牌列表
        }
    })

# ================= 2. 充值接口 =================
@auth_bp.route('/recharge', methods=['POST'])
def recharge():
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    
    if not user_id or amount is None: return jsonify({'code': 400}), 400
    user = db.session.get(User, user_id)
    if not user: return jsonify({'code': 404}), 404
    
    try:
        current = float(user.balance) if user.balance else 0.0
        user.balance = current + float(amount)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '充值成功', 'new_balance': user.balance})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 3. 获取个人信息 (含车牌) =================
@auth_bp.route('/profile', methods=['GET'])
def get_user_profile():
    user_id = request.args.get('user_id')
    user = db.session.get(User, user_id)
    if not user: return jsonify({'code': 404}), 404
    
    # === 从 Car 表查询 ===
    cars = Car.query.filter_by(user_id=user_id).all()
    plate_list = [c.plate_number for c in cars]
    
    return jsonify({
        'code': 200,
        'data': {
            'credit': user.credit_score,
            'balance': user.balance,
            'plates': plate_list # 返回列表
        }
    })

# ================= 4. 车牌管理 (增/删) =================
@auth_bp.route('/plate/update', methods=['POST'])
def update_plate():
    data = request.get_json()
    user_id = data.get('user_id')
    action = data.get('action') # 'add' 或 'remove'
    plate = data.get('plate')
    
    if not all([user_id, action, plate]):
        return jsonify({'code': 400, 'msg': '参数缺失'}), 400

    try:
        if action == 'add':
            # 查重：防止重复添加
            exists = Car.query.filter_by(user_id=user_id, plate_number=plate).first()
            if not exists:
                new_car = Car(user_id=user_id, plate_number=plate)
                db.session.add(new_car)
        
        elif action == 'remove':
            Car.query.filter_by(user_id=user_id, plate_number=plate).delete()
            
        db.session.commit()
        
        # 返回最新列表供前端更新
        cars = Car.query.filter_by(user_id=user_id).all()
        plate_list = [c.plate_number for c in cars]
        return jsonify({'code': 200, 'msg': '更新成功', 'plates': plate_list})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500

# ================= 5. 管理端获取用户列表 =================
@auth_bp.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.filter(User.role != 'admin').all()
    data = [{'id': u.user_id, 'username': u.username, 'real_name': u.real_name, 'credit': u.credit_score, 'balance': str(u.balance)} for u in users]
    return jsonify({'code': 200, 'data': data})

# ================= 6. 管理端修改用户 =================
@auth_bp.route('/admin/update_user', methods=['POST'])
def admin_update_user():
    data = request.get_json()
    user = db.session.get(User, data.get('user_id'))
    if not user: return jsonify({'code': 404}), 404
    try:
        if data.get('credit') is not None: user.credit_score = int(data.get('credit'))
        if data.get('balance') is not None: user.balance = float(data.get('balance'))
        db.session.commit()
        return jsonify({'code': 200})
    except: return jsonify({'code': 500}), 500