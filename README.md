# 智慧农业平台 (Smart Agriculture Platform)

面向多租户的SaaS化智慧农业全流程管理平台，采用LLM智能体技术实现温室大棚智能控制。

## 项目状态

**当前阶段**：Phase 1 - 基础架构搭建

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端Web | React + Ant Design |
| 前端小程序 | Uni-app (Vue) |
| 移动App | Flutter (V1.0后) |
| 后端API | Python FastAPI |
| LLM引擎 | MiniMax 2.5 |
| 物联网网关 | ThingsBoard / EMQX |
| 时序数据库 | TimescaleDB |
| 关系数据库 | PostgreSQL |
| 消息队列 | RabbitMQ |
| 缓存 | Redis |

## 核心功能

- 🌡️ 温室环境监测（温度、湿度、光照、CO2、土壤温湿度）
- 🤖 LLM智能控制中心（基于MiniMax 2.5的智能体）
- 📡 物联网设备管理（MQTT/Modbus/HTTP协议接入）
- 💧 水肥自动化管理
- 🛡️ 病虫害防治（图像识别 + LLM专家知识库）
- 💰 经济效益分析

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/joveli/smart-agriculture-platform.git
cd smart-agriculture-platform

# 启动后端
cd backend
docker-compose up -d

# 启动前端
cd frontend
npm install
npm run dev
```

## 项目文档

- [规格文档](./SPEC.md) - 完整功能规划
- [架构设计](./docs/architecture.md) - 系统架构说明

## 许可证

MIT License
