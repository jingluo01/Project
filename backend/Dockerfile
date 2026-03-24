# 使用官方 Python 运行时作为父镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1 

# === 新增：替换为阿里云源，加速下载 ===
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖 (为 cryptography 和其他可能的编译需求)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 设置入口脚本权限
RUN chmod +x entrypoint.sh

# 暴露端口
EXPOSE 5000

# 入口脚本
ENTRYPOINT ["./entrypoint.sh"]

# 启动命令 (作为 ENTRYPOINT 的参数)
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-k", "eventlet", "-b", "0.0.0.0:5000", "run:app"]
