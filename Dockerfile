# 使用 Python 3.10 基础镜像
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 创建必要的目录
RUN mkdir -p discussions memories logs
RUN touch discussions/.gitkeep memories/.gitkeep logs/.gitkeep

# 暴露端口
EXPOSE 9001

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令（使用 docker-compose 来管理多个服务）
CMD ["python", "-m", "src.religion_one_thinking.main"] 