"""
WebSocket 连接管理器
WebSocket Connection Manager - Tenant-isolated Rooms
"""

import asyncio
import json
from typing import Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict


class ConnectionInfo:
    """单个 WebSocket 连接信息"""

    def __init__(
        self,
        websocket: WebSocket,
        tenant_id: Optional[UUID] = None,
        greenhouse_ids: list[UUID] | None = None,  # None = 订阅全部
        user_id: Optional[UUID] = None,
    ):
        self.websocket = websocket
        self.tenant_id = tenant_id
        self.greenhouse_ids = greenhouse_ids  # None = 订阅该租户所有温室
        self.user_id = user_id


class WebSocketManager:
    """
    WebSocket 连接管理器

    功能：
    - 多租户隔离（每个租户只能收到自己温室的数据）
    - 温室级别订阅（可选）
    - 广播支持（告警全量推送）
    """

    def __init__(self):
        # tenant_id → list of connections
        self._tenant_connections: dict[str, list[ConnectionInfo]] = defaultdict(list)
        # greenhouse_id → list of connections（索引加速过滤）
        self._greenhouse_connections: dict[str, list[ConnectionInfo]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: Optional[str] = None,
        greenhouse_ids: list[str] | None = None,
        user_id: Optional[str] = None,
    ):
        """接受 WebSocket 连接并注册"""
        await websocket.accept()

        conn = ConnectionInfo(
            websocket=websocket,
            tenant_id=UUID(tenant_id) if tenant_id else None,
            greenhouse_ids=[UUID(g) for g in greenhouse_ids] if greenhouse_ids else None,
            user_id=UUID(user_id) if user_id else None,
        )

        async with self._lock:
            if tenant_id:
                self._tenant_connections[tenant_id].append(conn)
            if greenhouse_ids:
                for gid in greenhouse_ids:
                    self._greenhouse_connections[gid].append(conn)

        print(f"🔌 WebSocket connected: tenant={tenant_id}, greenhouses={greenhouse_ids}")

    async def disconnect(
        self,
        websocket: WebSocket,
        tenant_id: Optional[str] = None,
        greenhouse_ids: list[str] | None = None,
    ):
        """移除 WebSocket 连接"""
        async with self._lock:
            if tenant_id:
                self._tenant_connections[tenant_id] = [
                    c for c in self._tenant_connections[tenant_id]
                    if c.websocket != websocket
                ]
            if greenhouse_ids:
                for gid in greenhouse_ids:
                    self._greenhouse_connections[gid] = [
                        c for c in self._greenhouse_connections[gid]
                        if c.websocket != websocket
                    ]

    async def send_to_tenant(self, tenant_id: str, message: dict):
        """
        向指定租户的所有连接发送消息
        """
        connections = self._tenant_connections.get(tenant_id, []).copy()
        dead_connections = []

        for conn in connections:
            try:
                await conn.websocket.send_json(message)
            except Exception:
                dead_connections.append(conn)

        # 清理死连接
        if dead_connections:
            for conn in dead_connections:
                try:
                    await self.disconnect(
                        conn.websocket,
                        tenant_id=str(conn.tenant_id) if conn.tenant_id else None,
                        greenhouse_ids=[str(g) for g in conn.greenhouse_ids] if conn.greenhouse_ids else None,
                    )
                except Exception:
                    pass

    async def send_to_greenhouse(self, greenhouse_id: str, message: dict):
        """
        向指定温室的所有连接发送消息（包括订阅全温室的租户）
        """
        # 直接订阅该温室的连接
        direct_connections = self._greenhouse_connections.get(greenhouse_id, []).copy()

        # 订阅全温室的租户连接
        tenant_connections = []
        async with self._lock:
            for tenant_conns in self._tenant_connections.values():
                for conn in tenant_conns:
                    if conn.greenhouse_ids is None:  # 订阅全温室
                        tenant_connections.append(conn)

        all_connections = {id(c): c for c in direct_connections + tenant_connections}.values()
        dead = []

        for conn in all_connections:
            try:
                await conn.websocket.send_json(message)
            except Exception:
                dead.append(conn)

        if dead:
            for conn in dead:
                try:
                    await self.disconnect(
                        conn.websocket,
                        tenant_id=str(conn.tenant_id) if conn.tenant_id else None,
                    )
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        """
        全量广播（用于告警）
        """
        async with self._lock:
            all_connections = []
            for conns in self._tenant_connections.values():
                all_connections.extend(conns)

        dead = []
        for conn in all_connections:
            try:
                await conn.websocket.send_json(message)
            except Exception:
                dead.append(conn)

        if dead:
            for conn in dead:
                try:
                    await self.disconnect(
                        conn.websocket,
                        tenant_id=str(conn.tenant_id) if conn.tenant_id else None,
                    )
                except Exception:
                    pass

    def get_stats(self) -> dict:
        """获取连接统计"""
        total = sum(len(v) for v in self._tenant_connections.values())
        return {
            "total_connections": total,
            "tenant_count": len(self._tenant_connections),
            "greenhouse_count": len(self._greenhouse_connections),
        }


# 全局单例
ws_manager = WebSocketManager()
