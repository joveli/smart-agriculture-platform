"""
智慧农业平台 - FastAPI 应用入口
Smart Agriculture Platform - FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis
from app.core.rabbitmq import init_rabbitmq, close_rabbitmq
from app.core.mqtt_client import init_mqtt, close_mqtt
from app.api.v1 import auth, tenants, farms, greenhouses, devices, crops, alerts
from app.api.v1.admin import admin
from app.api.v1.agent import router as agent_router
from app.api.v1.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    await init_redis()
    await init_rabbitmq()

    # MQTT 订阅服务启动（后台任务）
    from app.core.mqtt_client import init_mqtt
    from app.services.sensor_data_service import get_sensor_data_service
    from app.services.alert_notification import get_alert_notification_service

    mqtt_client = await init_mqtt()
    sensor_service = get_sensor_data_service()
    await sensor_service.start()
    alert_service = get_alert_notification_service()
    await alert_service.start()

    # 将 MQTT 数据流接入传感器服务和规则引擎
    async def on_sensor_data(data: dict):
        await sensor_service.ingest(data)

    mqtt_client.add_data_handler(on_sensor_data)

    # 创建数据库表（Alembic 迁移前临时方案）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Application started (MQTT + SensorDataService + AlertNotification)")
    yield

    # 关闭时
    await close_mqtt()
    await sensor_service.stop()
    await close_redis()
    await close_rabbitmq()
    print("👋 Application shutdown")


app = FastAPI(
    title="智慧农业平台 API",
    description="面向多租户的SaaS化智慧农业全流程管理平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["租户管理"])
app.include_router(farms.router, prefix="/api/v1/farms", tags=["农场管理"])
app.include_router(greenhouses.router, prefix="/api/v1/greenhouses", tags=["温室管理"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["设备管理"])
app.include_router(crops.router, prefix="/api/v1/crops", tags=["作物管理"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["告警管理"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["超级管理员"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["LLM智能体"])
app.include_router(ws_router, prefix="/api/v1/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    return {"message": "智慧农业平台 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "Internal server error"},
    )
