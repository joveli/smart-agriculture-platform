# Backend - FastAPI

## 技术栈

- Python 3.11+
- FastAPI
- PostgreSQL
- TimescaleDB
- Redis
- RabbitMQ

## 本地开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d  # 启动依赖服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动服务后访问：http://localhost:8000/docs

## 环境变量

复制 `.env.example` 为 `.env` 并配置：

```
DATABASE_URL=postgresql://user:password@localhost:5432/smart_agriculture
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
MINIMAX_API_KEY=your_api_key
```

## 项目结构

```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据库模型
│   ├── schemas/      # Pydantic模型
│   ├── services/     # 业务逻辑
│   └── agents/       # LLM智能体
├── tests/            # 测试
├── deployments/      # 部署配置
└── requirements.txt
```
