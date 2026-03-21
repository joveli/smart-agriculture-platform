"""
WebSocket 流数据 API
WebSocket Stream API - Real-time Sensor Data & Alerts
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.services.websocket_manager import ws_manager

router = APIRouter()


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for auth"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID (if no token)"),
    greenhouse_ids: Optional[str] = Query(
        None,
        description="Comma-separated greenhouse IDs to subscribe (optional)"
    ),
):
    """
    WebSocket 实时数据流端点

    连接参数（URL query）：
    - token: JWT token（推荐，自动解析 tenant_id）
    - tenant_id: 租户ID（无 token 时必填）
    - greenhouse_ids: 温室ID列表，逗号分隔（可选，不填则订阅全部温室）

    订阅消息格式：
    ```json
    {"action": "subscribe", "greenhouse_ids": ["id1", "id2"]}
    {"action": "unsubscribe", "greenhouse_ids": ["id1"]}
    ```

    推送消息格式：
    ```json
    // 传感器数据
    {"type": "sensor_data", "greenhouse_id": "uuid", "data": {...}}
    // 告警
    {"type": "alert", "data": {...}}
    // 心跳
    {"type": "ping"}
    ```

    认证说明：
    - Phase 1: 暂不验证 token，依赖前端传 tenant_id
    - Phase 2: 完整 JWT 验证
    """
    # 解析参数
    parsed_tenant_id = None
    parsed_greenhouse_ids = None

    if token:
        # TODO: Phase 2 验证 JWT，提取 tenant_id
        # from app.core.security import decode_token
        # payload = decode_token(token)
        # parsed_tenant_id = payload.get("tenant_id")
        pass

    if tenant_id:
        try:
            UUID(tenant_id)
            parsed_tenant_id = tenant_id
        except ValueError:
            await websocket.close(code=4001, reason="Invalid tenant_id")
            return

    if greenhouse_ids:
        try:
            parsed_greenhouse_ids = [g.strip() for g in greenhouse_ids.split(",")]
            for gid in parsed_greenhouse_ids:
                UUID(gid)
        except ValueError:
            await websocket.close(code=4001, reason="Invalid greenhouse_ids")
            return

    if not parsed_tenant_id:
        await websocket.close(code=4001, reason="Missing tenant_id")
        return

    # 注册连接
    await ws_manager.connect(
        websocket=websocket,
        tenant_id=parsed_tenant_id,
        greenhouse_ids=parsed_greenhouse_ids,
    )

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "tenant_id": parsed_tenant_id,
            "greenhouse_ids": parsed_greenhouse_ids,
            "message": "WebSocket connected. Subscribed to sensor data stream."
        })

        # 保持连接，处理客户端消息
        while True:
            try:
                data = await websocket.receive_json()
                action = data.get("action")

                if action == "subscribe":
                    # 动态订阅温室
                    new_gids = data.get("greenhouse_ids", [])
                    for gid in new_gids:
                        UUID(gid)
                    # 重新注册
                    await ws_manager.disconnect(websocket, parsed_tenant_id, None)
                    await ws_manager.connect(
                        websocket=websocket,
                        tenant_id=parsed_tenant_id,
                        greenhouse_ids=new_gids,
                    )
                    await websocket.send_json({"type": "subscribed", "greenhouse_ids": new_gids})

                elif action == "unsubscribe":
                    # 取消订阅
                    await websocket.send_json({"type": "unsubscribed"})

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({"type": "error", "message": f"Unknown action: {action}"})

            except Exception as e:
                # 非 JSON 消息或断开
                break

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(
            websocket,
            tenant_id=parsed_tenant_id,
            greenhouse_ids=parsed_greenhouse_ids,
        )
        print(f"🔌 WebSocket disconnected: tenant={parsed_tenant_id}")
