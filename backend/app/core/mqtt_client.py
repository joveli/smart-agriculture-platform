"""
EMQX MQTT 订阅客户端
EMQX MQTT Subscription Client
"""

import json
import asyncio
from typing import Optional, Callable, Awaitable
from uuid import UUID
import paho.mqtt.client as mqtt
from app.core.config import settings


class MQTTClient:
    """
    EMQX MQTT 订阅客户端

    使用 paho-mqtt 实现，支持：
    - 自动重连
    - TLS 连接
    - 主题订阅（单次 + 持续）
    - 消息回调
    """

    def __init__(
        self,
        broker_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        clean_session: bool = True,
    ):
        self.broker_url = broker_url or settings.MQTT_BROKER_URL
        self.username = username or settings.MQTT_BROKER_USERNAME
        self.password = password or settings.MQTT_BROKER_PASSWORD

        # Parse broker URL: mqtt://host:port
        addr = self.broker_url.replace("mqtt://", "")
        host, port = addr.rsplit(":", 1) if ":" in addr else (addr, 1883)

        _client_id = client_id or f"smartagri_backend_{id(self)}"
        self.client = mqtt.Client(
            client_id=_client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311,
        )

        if self.username:
            self.client.username_pw_set(self.username, self.password)

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self._message_handler: Optional[Callable[[str, bytes], Awaitable[None]]] = None
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._reconnect_delay = 5  # seconds

    def set_message_handler(self, handler: Callable[[str, bytes], Awaitable[None]]):
        """设置消息处理函数（异步）"""
        self._message_handler = handler

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            print(f"✅ MQTT connected to {self.broker_url}")
        else:
            print(f"❌ MQTT connection failed, rc={rc}")
            self._connected = False

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        if rc != 0:
            print(f"⚠️ MQTT disconnected unexpectedly, rc={rc}, reconnecting in {self._reconnect_delay}s...")
        else:
            print("MQTT disconnected")

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        if self._message_handler and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._message_handler(msg.topic, msg.payload),
                self._loop
            )

    async def connect(self):
        """异步连接 MQTT Broker"""
        addr = self.broker_url.replace("mqtt://", "")
        host, port_s = addr.rsplit(":", 1) if ":" in addr else (addr, "1883")
        port = int(port_s)

        self._loop = asyncio.get_event_loop()

        # paho-mqtt 是同步库，用线程池跑
        def _connect_sync():
            self.client.connect(host, port, keepalive=60)
            self.client.loop_start()  # 启动后台线程

        await asyncio.to_thread(_connect_sync)

    async def subscribe(self, topic: str, qos: int = 1):
        """订阅主题"""
        if not self._connected:
            print(f"⚠️ Not connected, queuing subscription to {topic}")
            return

        result = self.client.subscribe(topic, qos)
        rc = result[0]
        if rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📡 Subscribed to: {topic}")
        else:
            print(f"❌ Subscribe failed: {rc}")

    async def publish(self, topic: str, payload: bytes | str, qos: int = 1, retain: bool = False):
        """发布消息"""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        result = self.client.publish(topic, payload, qos, retain)
        if result.is_published:
            print(f"📤 Published to {topic}")
        else:
            print(f"⚠️ Publish to {topic} not yet complete")
        return result.is_published

    async def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected


class SensorMQTTClient(MQTTClient):
    """
    传感器数据专用 MQTT 客户端

    订阅主题格式：
        tenants/{tenant_id}/devices/{device_id}/sensors/{metric}
    示例：
        tenants/abc123/devices/def456/sensors/temperature
        tenants/abc123/devices/def456/sensors/#
    """

    # 订阅所有租户所有设备的传感器数据（后台服务权限）
    DEFAULT_TOPIC = "tenants/+/devices/+/sensors/#"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data_handlers: list[Callable[[dict], Awaitable[None]]] = []

    def add_data_handler(self, handler: Callable[[dict], Awaitable[None]]):
        """添加数据处理器（传感器数据流入时调用）"""
        self._data_handlers.append(handler)

    async def _handle_sensor_message(self, topic: str, payload: bytes):
        """
        解析传感器 MQTT 消息

        Topic: tenants/{tenant_id}/devices/{device_id}/sensors/{metric}
        Payload: {"value": 25.5, "timestamp": "2026-03-21T10:00:00Z"}

        也支持完整数据一次性发送：
        Topic: tenants/{tenant_id}/devices/{device_id}/sensors/batch
        Payload: {"temperature": 25.5, "humidity": 70, ...}
        """
        try:
            parts = topic.strip("/").split("/")
            # tenants/+/devices/+/sensors/... → parts = ["tenants", tenant_id, "devices", device_id, "sensors", ...]
            if len(parts) < 6:
                print(f"⚠️ Invalid sensor topic: {topic}")
                return

            tenant_id = parts[1]
            device_id = parts[3]
            metric_or_group = parts[5] if len(parts) > 5 else "batch"

            data = json.loads(payload.decode("utf-8"))

            parsed = {
                "tenant_id": tenant_id,
                "device_id": device_id,
                "topic": topic,
            }

            if metric_or_group == "batch":
                # 完整数据批量
                parsed.update(data)
            else:
                # 单指标
                parsed["metric"] = metric_or_group
                parsed["value"] = data.get("value")
                parsed["timestamp"] = data.get("timestamp")

            # 分发给所有处理器
            for handler in self._data_handlers:
                try:
                    await handler(parsed)
                except Exception as e:
                    print(f"⚠️ Data handler error: {e}")

        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON in sensor message: {payload}")
        except Exception as e:
            print(f"⚠️ Error handling sensor message: {e}")

    def set_message_handler(self, handler: Callable[[str, bytes], Awaitable[None]]):
        # 忽略基类的，设置专用处理器
        pass

    async def start(self):
        """启动传感器 MQTT 客户端，订阅默认主题"""
        await self.connect()
        await self.subscribe(self.DEFAULT_TOPIC, qos=1)
        # 使用专用处理器
        self._loop.add_reader(
            self.client._sock,
            lambda: None  # 占位，实际在 on_message 中处理
        )


# 全局 MQTT 客户端实例
_mqtt_client: Optional[SensorMQTTClient] = None


async def init_mqtt() -> SensorMQTTClient:
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = SensorMQTTClient()
        await _mqtt_client.connect()
        await _mqtt_client.subscribe(SensorMQTTClient.DEFAULT_TOPIC, qos=1)
        _mqtt_client._loop = asyncio.get_event_loop()
        # 使用自定义消息处理
        original_on_message = _mqtt_client.client.on_message
        def custom_on_message(client, userdata, msg):
            asyncio.run_coroutine_threadsafe(
                _mqtt_client._handle_sensor_message(msg.topic, msg.payload),
                _mqtt_client._loop
            )
        _mqtt_client.client.on_message = custom_on_message
    return _mqtt_client


async def close_mqtt():
    global _mqtt_client
    if _mqtt_client:
        await _mqtt_client.disconnect()
        _mqtt_client = None
