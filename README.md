# 🅿️ 智慧校园停车场预约与管理系统 (Smart Parking)

[![Vue](https://img.shields.io/badge/Vue.js-3.x-4fc08d.svg?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg?style=flat-square&logo=mysql)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)

基于 **Vue 3 (Vite)** + **Flask** + **Three.js** 开发的现代化全栈项目。系统集成了 3D 数字化孪生地图、实时 WebSocket 状态推送、智能阶梯计费与信用风控体系，为校园停车提供闭环式管理方案。

---

## 🌟 核心亮点 (Key Features)

### 🎨 交互与视觉
- **3D 数字化孪生**: 采用 Three.js 原生构建 3D 停车地图，支持车位状态实时渲染与交互式预约。
- **响应式设计**: 完全适配移动端与 PC 端，提供极致流畅的用户体验。
- **实时同步**: 基于 WebSocket 的毫秒级数据推送，确保车位占用情况多端实时一致。

### 💳 业务逻辑
- **多角色计费**: 自动识别学生、教职工、访客身份，支持差异化折扣与阶梯式计费算法。
- **信用风控**: 深度集成信用评分体系，支持违约自动扣分、异常订单判定及预约权限限制。
- **售后保障**: 新增**在线退款申请**（24小时限时）与管理员一键审批原路退回功能。

### 🛠️ 效率管理
- **高级数据导出**: 支持全量订单记录导出为 **Excel (.xlsx)** 与 **CSV** 格式，解决长文本折叠排版问题。
- **车牌自动识别**: 模拟 AI 视觉入场/离场识别逻辑，支持快速入场与自动出场计费。
- **全方位监控**: 提供营收统计、车位利用率分析、活跃用户趋势等可视化图表。

---

## 📸 界面预览 (Screenshots)

*   **三维直观地图**: `IfcViewer` 驱动的 3D 实景选位
*   **管理透视镜**: 订单多维筛选、退款待办提醒、多格式一键导出
*   **用户口袋**: 车辆管理、余额充值、历史账单透明化

---

## 🏗️ 技术架构 (Architecture)

| 模块 | 关键技术 |
| :--- | :--- |
| **前端 (Frontend)** | Vue 3, Vite 5, Element Plus, Pinia, ECharts 5, Three.js, Socket.io-client |
| **后端 (Backend)** | Flask 3.0, SQLAlchemy Core, JWT Auth, Flask-SocketIO, APScheduler |
| **存储 (Storage)** | MySQL 8.0 (持久化), Redis (高速缓存/分布式锁) |
| **部署 (DevOps)** | Docker Compose (一键编排) |

---

## 🚀 快速开始 (Getting Started)

### 1. 环境准备 (Prerequisites)
- **Node.js**: 16.x + (推荐 18.x)
- **Python**: 3.8 +
- **MySQL**: 8.0 +
- **Redis**: 6.x +

### 2. 数据库配置 (Database)
创建名为 `campus_parking` 的数据库：
```sql
CREATE DATABASE campus_parking CHARACTER SET utf8mb4;
```

### 3. 后端初始化 (Backend Setup)
```bash
cd backend
# 创建并激活虚拟环境
python -m venv venv
./venv/Scripts/activate  # MacOS/Linux: source venv/bin/activate

# 安装组件
pip install -r requirements.txt

# 配置环境变量 (填写数据库与 Redis 地址)
cp .env.example .env

# 初始化表结构结构与种子数据
python init_db.py

# 启动 (默认 5000 端口)
python run.py
```

### 4. 前端启动 (Frontend Setup)
```bash
cd frontend
# 安装依赖
npm install --legacy-peer-deps

# 启动开发服务器 (默认 5173 端口)
npm run dev
```

### 🐳 5. Docker 一键部署 (Docker Compose)
如果您已安装 Docker，推荐使用 Compose 进行一键环境编排：

```bash
# 进入项目根目录直接启动
docker-compose up -d --build
```
*   **前端访问**: http://localhost:80
*   **后端 API**: http://localhost:5000
*   **数据库初始化**: 容器首次启动时，会自动执行 `backend/init_db.py` 逻辑（请参考 `docker-compose.yml` 配置）。

---

## 👤 测试账号 (Test Accounts)

| 身份 | 账号 (user_no) | 密码 | 初始权限与状态 |
| :--- | :--- | :--- | :--- |
| **管理员** | `admin` | `admin123` | 营收分析、订单审核、导出权限 |
| **学生** | `2021001` | `123456` | 9折优惠、实名车辆、部分预存 |
| **教师** | `T2021001` | `123456` | 8折优惠、VIP 权限 |

---

## 🔧 配置指南 (Configuration)

### 后端 `.env` 参数
- `DATABASE_URL`: 格式为 `mysql+pymysql://user:pass@host:port/db_name`
- `REDIS_URL`: 缓存与 Socket 共享地址
- `ROLE_DISCOUNT`: 可在 `config.py` 中自定义角色折扣比例

### 💳 支付宝支付集成 (Alipay Setup)
本系统集成了支付宝沙箱支付环境，配置步骤如下：
1.  登录 [支付宝开放平台-沙箱环境](https://open.alipay.com/develop/sandbox/app)。
2.  获取 `APPID` 并填入 `.env`。
3.  生成 RSA2 密钥对，将 **应用私钥** 填入 `ALIPAY_PRIVATE_KEY`。
4.  在沙箱配置界面获取 **支付宝公钥**（注意不是应用公钥），填入 `ALIPAY_PUBLIC_KEY`。
5.  默认网关使用沙箱地址：`https://openapi-sandbox.dl.alipaydev.com/gateway.do`。

### 3D 地图自定义
地图模型位于 `frontend/public/*.ifc`，可通过 `IfcViewer.vue` 中的 `buildNativeScene` 逻辑自定义渲染布局。

---

## 📄 许可证
本项目采用 [MIT License](LICENSE).

## 👥 贡献
诚邀贡献！请提交 PR 或开 Issue。
