# 智慧农业平台 - 部署文档

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 服务器：1CPU / 2GB RAM 最低配置
- 端口：80, 5432, 6379, 5672, 1883, 8083, 8084, 9000, 9001, 8000, 18083

## 快速部署

### 1. 克隆仓库

```bash
cd /opt
git clone https://github.com/joveli/smart-agriculture-platform.git
cd smart-agriculture-platform
```

### 2. 配置环境变量

```bash
cp .env.production.example .env
# 编辑 .env 填入真实密码和密钥
```

### 3. 一键启动

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. 验证

```bash
# 后端健康检查
curl http://localhost:8000/health

# EMQX Dashboard
# 浏览器访问 http://localhost:18083 （admin/public）

# MinIO Console
# 浏览器访问 http://localhost:9001 （smartagri/smartagri_secret）

# 前端
# 浏览器访问 http://localhost
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 Nginx | 80 | Web 管理后台 |
| FastAPI | 8000 | API 服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| RabbitMQ | 5672/15672 | 消息队列 |
| EMQX | 1883/8083/8084/18083 | MQTT Broker + Dashboard |
| MinIO | 9000/9001 | 对象存储 + Console |

## 常用运维命令

```bash
# 查看所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 重启服务
docker-compose -f docker-compose.prod.yml restart backend

# 更新部署
git pull origin master
docker-compose -f docker-compose.prod.yml up -d --build

# 停止服务
docker-compose -f docker-compose.prod.yml down
```

## 数据库初始化

首次启动后，执行数据库迁移：

```bash
docker exec smart_agri_backend alembic upgrade head
```

## 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 8000/tcp # API
sudo ufw allow 1883/tcp # MQTT
sudo ufw allow 8083/tcp # MQTT WebSocket
sudo ufw allow 9000/tcp # MinIO API

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 健康检查

所有服务健康检查：

```bash
# 1. 后端
curl -f http://localhost:8000/health

# 2. PostgreSQL
docker exec smart_agri_postgres pg_isready -U smartagri

# 3. Redis
docker exec smart_agri_redis redis-cli ping

# 4. RabbitMQ
curl -s -u smartagri:smartagri_secret http://localhost:15672/api/health/checks/alarms

# 5. EMQX
curl -s http://localhost:18083/api/v5/status
```

## 备份

```bash
# 数据库备份
docker exec smart_agri_postgres pg_dump -U smartagri smart_agriculture > backup_$(date +%Y%m%d).sql

# MinIO 数据备份
docker run --rm -v minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup.tar.gz -C /data .
```
