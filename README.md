# 🎓 校园智能停车系统 (Campus Parking System)

基于 Vue3 + Flask + MySQL 开发的校园停车预约与管理系统。
本项目为计算机专业毕业设计作品。

## ✨ 功能特性

### 🚗 用户端 (Client)
- **车位地图**：实时查看 A/B/C 三区的车位状态（空闲/占用/预约）。
- **在线预约**：支持选择绑定车辆进行预约，系统自动生成订单。
- **个人中心**：钱包充值、多车辆管理（云端同步）、信用分查看。
- **智能交互**：模拟车辆入场识别、出场费用结算（支持余额/扫码支付）。

### 📊 管理端 (Admin)
- **数据驾驶舱**：ECharts 可视化展示营收趋势、车位利用率。
- **用户风控**：查看用户列表，支持修改信用分（触发系统拦截）。
- **全局订单**：查看全校停车记录，支持按条件搜索及 **导出 Excel**。
- **系统设置**：动态调整停车费率（元/分钟）。

## 🛠️ 技术栈

- **前端**：Vue 3, Vite, Vue Router, Element Plus, Axios, ECharts
- **后端**：Python 3.9+, Flask, SQLAlchemy, MySQL
- **数据库**：MySQL 8.0

## 🚀 快速开始

### 1. 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
python run.py

检查每个页面的ui，调整其中不合理的布局