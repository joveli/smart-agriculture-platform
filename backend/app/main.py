"""
智慧农业平台 - FastAPI 应用入口
Smart Agriculture Platform - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import auth, tenants, farms, greenhouses, devices, crops, alerts

app = FastAPI(
    title="智慧农业平台 API",
    description="面向多租户的SaaS化智慧农业全流程管理平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
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


@app.get("/")
async def root():
    return {"message": "智慧农业平台 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
