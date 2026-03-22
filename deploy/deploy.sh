#!/bin/bash
# Smart Agriculture Platform - Deploy Script for 192.168.3.101
# Usage: ./deploy.sh

set -e

APP_DIR="/opt/smart-agriculture"
REPO_URL="https://github.com/joveli/smart-agriculture-platform.git"

echo "=== 智慧农业平台部署脚本 ==="
echo "目标服务器: 192.168.3.101"
echo ""

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker 未安装"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "[ERROR] Docker 未运行"
    exit 1
fi

echo "[OK] Docker 已就绪"

# 2. 创建目录
echo "[INFO] 创建应用目录..."
sudo mkdir -p $APP_DIR
cd $APP_DIR

# 3. 拉取代码
if [ -d ".git" ]; then
    echo "[INFO] 更新代码..."
    git pull origin master
else
    echo "[INFO] 克隆仓库..."
    sudo git clone $REPO_URL $APP_DIR
fi

# 4. 配置环境变量
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[INFO] 创建环境变量配置..."
    sudo cp $APP_DIR/.env.production.example $APP_DIR/.env
    echo "[WARN] 请编辑 $APP_DIR/.env 填入真实密码和密钥"
    echo "[WARN] 然后重新运行: docker-compose -f docker-compose.prod.yml up -d"
    exit 1
fi

# 5. 拉取镜像
echo "[INFO] 拉取最新镜像..."
docker-compose -f docker-compose.prod.yml pull

# 6. 启动服务
echo "[INFO] 启动服务..."
docker-compose -f docker-compose.prod.yml up -d --build

# 7. 等待服务启动
echo "[INFO] 等待服务启动 (30s)..."
sleep 30

# 8. 健康检查
echo "[INFO] 执行健康检查..."
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "[OK] 后端服务正常"
else
    echo "[WARN] 后端服务可能未就绪，请检查: docker-compose -f docker-compose.prod.yml logs backend"
fi

echo ""
echo "=== 部署完成 ==="
echo "前端:      http://192.168.3.101"
echo "API:       http://192.168.3.101:8000"
echo "EMQX:     http://192.168.3.101:18083 (admin/public)"
echo "MinIO:    http://192.168.3.101:9001"
echo "RabbitMQ: http://192.168.3.101:15672"
echo ""
