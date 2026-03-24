# 智慧校园停车场系统 - 部署指南

本指南将帮助你将项目部署到 Linux 服务器（CentOS/Ubuntu/Debian）。

## 1. 准备工作

确保你的服务器已安装：
- **Docker**: [安装教程](https://docs.docker.com/engine/install/)
- **Docker Compose**: [安装教程](https://docs.docker.com/compose/install/)

## 2. 上传文件

将本地项目目录上传到服务器（建议使用 FileZilla 或 scp 命令）。
**注意**：不需要上传 `venv` (Python虚拟环境) 和 `frontend/node_modules` (前端依赖)，也不需要 `frontend/dist`，因为这些都会在 Docker 中重新构建。

示例 SCP 命令：
```bash
# 在你本地电脑的终端执行
# 假设服务器IP是 1.2.3.4，用户是 root，目标路径是 /opt/parking
scp -r ./Project root@1.2.3.4:/opt/parking
```

## 3. 启动服务

登录到服务器，进入项目目录：

```bash
cd /opt/parking
```

执行一键启动命令（这会自动构建镜像并启动所有服务）：

```bash
docker compose up -d --build
```

查看服务状态：
```bash
docker compose ps
```
你应该能看到 `frontend`, `backend`, `mysql`, `redis` 四个容器都在 Running 状态。

## 4. 初始化数据 (首次部署特别说明)

本系统已通过 `backend/entrypoint.sh` **实现了自动初始化检测**：
- 当后端容器启动时，会自动等待 MySQL 就绪。
- 系统会自动执行 `python init_db.py`。
- 如果数据库已有用户（非首次启动），初始化脚本会自动跳过，**不会覆盖现有数据**。

**手动强行初始化或修复数据：**
如果您需要手动重新导入师生基础数据：
```bash
docker compose exec backend python init_school_db.py
```
看到 "Success" 字样即可。

## 5. 访问系统

打开浏览器访问你的服务器 IP：
`http://你的服务器IP`

- **管理员账号**: `admin` / `admin123`
- **学生账号**: `2021001` / `123456`

## 6. 查看日志 & 维护

在服务器运行期间，你可能需要查看日志来排查问题。

### 查看后端日志 (Flask/Gunicorn)
```bash
# 查看最后200行并持续刷新
docker compose logs -f --tail=200 backend
```
如果看到报错，通常能在这里找到 Python 的 Traceback。

### 查看前端/Nginx 日志
前端不仅是页面，还包含了 Nginx 作为反向代理的访问日志。
```bash
# 查看访问日志
docker compose logs -f frontend
```
如果你发现接口报 404 或 502 Bad Gateway，请重点检查这里的日志。

### 查看数据库日志
```bash
docker compose logs -f mysql
```

## 常见问题

### 1. 验证码/支付报错 SSL
如果服务器无法访问外网（尤其是支付宝沙箱），可能会导致支付功能报错。
查看日志命令：
```bash
docker-compose logs -f backend
```

### 2. 端口冲突
如果 80 或 3306 端口被占用，请修改 `docker-compose.yml` 中的端口映射。
例如将前端映射改为 8080:80。

### 3. 持久化数据
数据库文件存放在 Docker Volume 中，即使删除容器数据也不会丢失。
如需彻底重置，请运行：
```bash
docker compose down -v
```

## 9. 逆向迁移指南 (从服务器回拉到本地)

如果你想把服务器上运行的**最新数据**或**修改过的代码**拉回本地电脑，请按以下步骤操作。

### 1. 拉取代码和文件 (SCP)
如果你在服务器上直接修改了代码，或者想下载上传的图片/日志：

在**本地电脑终端**执行 (将 `/opt/parking` 替换为你服务器上的路径)：
```bash
# 将服务器的 /opt/parking 整个目录下载到本地的 server_backup 文件夹
scp -r root@47.110.81.78:/opt/parking ./server_backup
```

### 2. 拉取数据库数据
如果你想分析服务器产生的真实业务数据：

**第一步：在服务器上导出数据**
登录服务器终端，进入项目目录执行：
```bash
# 导出 SQL 文件
docker compose exec mysql mysqldump -u root -p123456 campus_parking > campus_parking_prod.sql
docker compose exec mysql mysqldump -u root -p123456 school_official > school_official_prod.sql
```

**第二步：下载 SQL 文件到本地**
在**本地电脑终端**执行：
```bash
scp root@47.110.81.78:/opt/parking/*_prod.sql ./
```

**第三步：导入本地数据库**
```bash
# 假设你本地用 Docker 跑数据库
cat campus_parking_prod.sql | docker compose exec -T mysql mysql -u root -p123456 campus_parking

# 或者如果你本地是直接安装的 MySQL (如 python run.py 用户)
# mysql -u root -p123456 campus_parking < campus_parking_prod.sql
```
