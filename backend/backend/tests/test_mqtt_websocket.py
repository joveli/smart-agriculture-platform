"""
MQTT + WebSocket 服务单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.sensor_data_service import SensorDataService
from app.services.websocket_manager import WebSocketManager, ConnectionInfo


class TestSensorDataService:
    """SensorDataService 测试"""

    @pytest.fixture
    def service(self):
        return SensorDataService(batch_size=5, flush_interval_sec=1.0)

    def test_normalize_batch_data(self, service):
        """测试批量数据规范化"""
        data = {
            "tenant_id": str(uuid4()),
            "device_id": str(uuid4()),
            "temperature": 25.5,
            "humidity": 70.0,
            "light": 45000,
        }
        result = service._normalize_data(data)
        assert result is not None
        assert result["temperature"] == 25.5
        assert result["humidity"] == 70.0
        assert result["light"] == 45000

    def test_normalize_missing_fields(self, service):
        """测试缺失字段返回 None"""
        data = {
            "tenant_id": str(uuid4()),
            # missing device_id
        }
        result = service._normalize_data(data)
        assert result is None

    def test_to_float(self, service):
        """测试浮点转换"""
        assert service._to_float(25.5) == 25.5
        assert service._to_float("25.5") == 25.5
        assert service._to_float(None) is None
        assert service._to_float("invalid") is None


class TestWebSocketManager:
    """WebSocketManager 测试"""

    @pytest.fixture
    def manager(self):
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, manager, mock_websocket):
        """测试连接和断开"""
        tenant_id = str(uuid4())
        await manager.connect(mock_websocket, tenant_id=tenant_id)

        assert len(manager._tenant_connections[tenant_id]) == 1

        await manager.disconnect(mock_websocket, tenant_id=tenant_id)
        assert len(manager._tenant_connections[tenant_id]) == 0

    @pytest.mark.asyncio
    async def test_send_to_tenant(self, manager, mock_websocket):
        """测试向租户发送消息"""
        tenant_id = str(uuid4())
        await manager.connect(mock_websocket, tenant_id=tenant_id)

        message = {"type": "test", "data": "hello"}
        await manager.send_to_tenant(tenant_id, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, manager, mock_websocket):
        """测试租户隔离"""
        tenant_a = str(uuid4())
        tenant_b = str(uuid4())

        ws_a = AsyncMock()
        ws_a.send_json = AsyncMock()
        ws_b = AsyncMock()
        ws_b.send_json = AsyncMock()

        await manager.connect(ws_a, tenant_id=tenant_a)
        await manager.connect(ws_b, tenant_id=tenant_b)

        await manager.send_to_tenant(tenant_a, {"type": "a_only"})
        ws_a.send_json.assert_called_once_with({"type": "a_only"})
        ws_b.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """测试全量广播"""
        tenants = [str(uuid4()) for _ in range(3)]
        websockets = []
        for tid in tenants:
            ws = AsyncMock()
            ws.send_json = AsyncMock()
            await manager.connect(ws, tenant_id=tid)
            websockets.append((tid, ws))

        message = {"type": "broadcast", "alert": True}
        await manager.broadcast(message)

        for tid, ws in websockets:
            ws.send_json.assert_called_with(message)

    def test_stats(self, manager):
        """测试连接统计"""
        stats = manager.get_stats()
        assert "total_connections" in stats
        assert "tenant_count" in stats


class TestSensorDataServiceIntegration:
    """SensorDataService 集成测试（带 mock 数据库）"""

    @pytest.mark.asyncio
    async def test_ingest_triggers_flush_on_batch_size(self):
        """测试达到 batch_size 时触发刷盘"""
        service = SensorDataService(batch_size=3, flush_interval_sec=60.0)

        with patch.object(service, "_flush", new_callable=AsyncMock) as mock_flush:
            for i in range(3):
                await service.ingest({
                    "tenant_id": str(uuid4()),
                    "device_id": str(uuid4()),
                    "temperature": 20.0 + i,
                })
            # 第三次 ingest 会触发 flush
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_ignores_invalid_data(self):
        """测试忽略无效数据"""
        service = SensorDataService(batch_size=100, flush_interval_sec=60.0)

        with patch.object(service, "_flush", new_callable=AsyncMock) as mock_flush:
            await service.ingest({
                "tenant_id": str(uuid4()),
                # missing device_id
            })
            # 不应触发 flush
            mock_flush.assert_not_called()
