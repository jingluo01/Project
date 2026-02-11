# 智慧校园停车场预约与管理系统

基于 Vue 3 + Flask 的全栈校园停车场管理系统，实现实时车位预约、智能计费、信用风控等功能。

## 📸 系统截图

系统包含三个主要界面：

1. **登录页面** - 优雅的渐变设计，支持学生/教师/管理员登录
2. **用户停车地图** - 实时显示车位状态，支持在线预约，信用积分和余额展示
3. **管理员仪表盘** - 营收统计、用户管理、车位监控、订单管理

## ✨ 核心功能

### 用户端功能
- ✅ 用户注册/登录（学生、教职工、访客）
- ✅ 实时车位地图展示（A/B/C 区域切换）
- ✅ 在线预约车位（悲观锁防止超卖）
- ✅ 车辆管理（绑定/解绑多辆车）
- ✅ 钱包充值
- ✅ 订单历史查询
- ✅ 信用分系统
- ✅ WebSocket 实时车位状态推送

### 管理员功能
- ✅ 仪表盘数据统计（营收、活跃用户、订单数）
- ✅ 营收趋势图表（ECharts）
- ✅ 车位利用率分析
- ✅ 用户管理（信用分调整、账号封禁）
- ✅ 车位管理（状态调整、费率设置）
- ✅ 订单管理

### 技术亮点
- 🔒 **并发控制** - 使用数据库悲观锁（`SELECT ... FOR UPDATE`）防止车位超卖
- 🔄 **实时通信** - WebSocket 实现车位状态毫秒级实时推送
- 💳 **智能计费** - 基于停车时长、角色折扣的自动计费
- 🎯 **信用风控** - 超时未支付自动扣除信用分，限制预约权限
- 📊 **数据可视化** - ECharts 图表展示营收趋势和利用率

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Flask 3.0
- **ORM**: SQLAlchemy
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **实时通信**: Flask-SocketIO
- **认证**: JWT
- **定时任务**: APScheduler

### 前端技术栈
- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 5
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts 5
- **实时通信**: Socket.IO Client
- **HTTP 客户端**: Axios

### 数据库设计
- `sys_user` - 用户表（学号、角色、余额、信用分）
- `car` - 车辆表（人车分离设计）
- `parking_zone` - 停车区域表（费率、免费时长）
- `parking_spot` - 车位表（状态、当前车牌）
- `parking_order` - 订单表（完整生命周期追踪）

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0
- Redis

### 1. 启动数据库和 Redis

```bash
# 使用 Docker Compose 启动
docker-compose up -d
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp ../.env.example .env

# 初始化数据库
python init_db.py

# 启动后端服务
python run.py
```

后端将运行在 `http://localhost:5000`

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

## 👤 测试账号

系统已预置以下测试账号：

| 角色 | 学号/工号 | 密码 | 说明 |
|------|----------|------|------|
| 管理员 | admin | admin123 | 完整系统管理权限 |
| 学生 | 2021001 | 123456 | 9折优惠，已绑定车辆 京A88888 |
| 教职工 | T2021001 | 123456 | 8折优惠，已绑定车辆 京B12345 |

## 📋 核心业务流程

### 1. 预约流程
```
选择车位 → 风控检查（信用分、未支付订单） → 悲观锁锁定车位 → 创建订单 → WebSocket 推送状态更新
```

### 2. 入场流程
```
车牌识别 → 查找预约订单 → 订单状态变更（已预约→进行中） → 车位状态变更（已预约→占用） → 记录入场时间
```

### 3. 出场流程
```
车牌识别 → 查找进行中订单 → 计算费用（时长×费率×折扣） → 信用分判断 → 自动扣款/待支付 → 释放车位
```

### 4. 违约处理
```
24小时未支付 → 定时任务检测 → 订单标记违约 → 扣除信用分20分 → 限制预约权限
```

## 🔧 配置说明

### 环境变量配置 (.env)

```env
# Flask 配置
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/campus_parking

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# CORS 配置
CORS_ORIGINS=http://localhost:5173
```

### 业务规则配置 (backend/config.py)

```python
PAYMENT_TIMEOUT_HOURS = 24  # 支付超时时间
CREDIT_PENALTY = 20  # 违约扣除信用分
MIN_CREDIT_SCORE = 80  # 最低信用分要求
PERFECT_CREDIT_SCORE = 100  # 完美信用分

# 角色折扣
ROLE_DISCOUNT = {
    0: 1.0,   # 外部用户，无折扣
    1: 0.9,   # 学生，9折
    2: 0.8,   # 教职工，8折
}
```

## 📁 项目结构

```
campus-parking/
├── backend/                 # 后端 Flask 应用
│   ├── app/
│   │   ├── models/         # 数据库模型
│   │   ├── blueprints/     # API 蓝图
│   │   ├── utils/          # 工具函数
│   │   └── tasks/          # 后台任务
│   ├── config.py           # 配置文件
│   ├── run.py              # 启动入口
│   └── init_db.py          # 数据库初始化
├── frontend/               # 前端 Vue 应用
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 可复用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # API 请求封装
│   │   ├── utils/          # 工具函数
│   │   └── router/         # 路由配置
│   └── vite.config.js      # Vite 配置
└── docker-compose.yml      # Docker 编排
```

## 🔐 安全特性

- JWT Token 认证
- 密码 Hash 存储（Werkzeug）
- CORS 跨域保护
- SQL 注入防护（SQLAlchemy ORM）
- XSS 防护（Vue 自动转义）

## 🧪 测试建议

### 并发预约测试
1. 打开多个浏览器窗口
2. 使用不同账号同时预约同一车位
3. 验证只有一个用户成功，其他用户收到"车位已被抢"提示

### 信用风控测试
1. 创建订单但不支付
2. 等待24小时或手动修改数据库时间
3. 运行定时任务检查
4. 验证订单变为违约状态，信用分扣除

### 实时推送测试
1. 打开两个浏览器窗口
2. 在一个窗口预约车位
3. 验证另一个窗口实时看到车位状态变化

## 📝 API 文档

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/reset-password` - 密码重置

### 用户接口
- `GET /api/user/profile` - 获取个人信息
- `POST /api/user/car/bind` - 绑定车辆
- `DELETE /api/user/car/remove/:id` - 解绑车辆
- `POST /api/user/recharge` - 钱包充值

### 停车场接口
- `GET /api/parking/zones` - 获取停车区域
- `GET /api/parking/spots` - 获取车位状态
- `POST /api/parking/enter` - 车辆入场
- `POST /api/parking/exit` - 车辆出场

### 订单接口
- `POST /api/order/create` - 创建订单
- `POST /api/order/pay` - 支付订单
- `POST /api/order/cancel` - 取消订单
- `GET /api/order/list` - 订单列表

### 管理员接口
- `GET /api/admin/stats` - 仪表盘统计
- `GET /api/admin/users` - 用户列表
- `POST /api/admin/user/update` - 更新用户
- `POST /api/admin/parking/update` - 更新车位
- `GET /api/admin/orders` - 所有订单

## 🛠️ 开发指南

### 添加新的停车区域

```python
# backend/init_db.py
new_zone = ParkingZone(
    zone_name='D区(体育馆)',
    fee_rate=4.00,
    free_time=20
)
db.session.add(new_zone)
db.session.commit()
```

### 自定义费率计算

修改 `backend/app/utils/fee_calculator.py` 中的 `calculate_parking_fee` 函数

### 调整信用分规则

修改 `backend/config.py` 中的 `CREDIT_PENALTY` 和 `MIN_CREDIT_SCORE`

## 🐛 常见问题

### 1. WebSocket 连接失败
- 检查后端是否使用 `eventlet` 启动
- 确认前端代理配置正确
- 检查防火墙设置

### 2. 数据库连接失败
- 确认 MySQL 服务已启动
- 检查 `.env` 中的数据库配置
- 验证数据库用户权限

### 3. 前端无法访问后端 API
- 检查 Vite 代理配置
- 确认后端 CORS 设置
- 验证后端服务运行状态

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请通过 Issue 反馈。
