"""
告警通知服务
Alert Notification Service - RabbitMQ Fanout + WebSocket
"""

import asyncio
import json
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.core.rabbitmq import get_alert_exchange
from app.services.websocket_manager import ws_manager


class AlertNotificationService:
    """
    告警通知服务

    功能：
    - 监听 RabbitMQ 告警消息
    - 通过 WebSocket 推送给前端
    - 通过钉钉/飞书 Webhook 通知外部群
    - 记录通知历史
    """

    def __init__(self):
        self._webhook_urls: dict[str, str] = {
            # "tenant_id": "https://oapi.dingtalk.com/robot/send?access_token=..."
        }
        self._webhook_cache: dict[str, Optional[dict]] = {}  # tenant_id -> webhook config
        self._http_client: Optional[asyncio.AbstractEventLoop] = None

    async def start(self):
        """启动通知服务（注册 RabbitMQ consumer）"""
        print("✅ AlertNotificationService started")

    async def notify_alert(
        self,
        alert: Alert,
        db: AsyncSession,
    ):
        """
        发送告警通知（被规则引擎调用）

        流程：
        1. WebSocket 推送（所有连接）
        2. 钉钉/飞书 Webhook（异步 HTTP POST）
        """
        # 1. WebSocket 广播（租户内）
        ws_message = {
            "type": "alert",
            "data": {
                "id": str(alert.id),
                "greenhouse_id": str(alert.greenhouse_id),
                "alert_type": alert.alert_type,
                "level": alert.level,
                "message": alert.message,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
        }
        await ws_manager.send_to_tenant(str(alert.tenant_id), ws_message)

        # 2. 外部 Webhook 通知
        await self._send_webhook(alert)

    async def _send_webhook(self, alert: Alert):
        """发送钉钉/飞书 Webhook 通知"""
        webhook_config = await self._get_webhook_config(alert.tenant_id)
        if not webhook_config:
            return

        url = webhook_config.get("url")
        platform = webhook_config.get("platform", "dingtalk")  # dingtalk | feishu

        if not url:
            return

        # 构建消息体
        level_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
        emoji = level_emoji.get(alert.level, "📢")

        if platform == "dingtalk":
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{emoji} 智慧农业告警",
                    "text": f"## {emoji} {alert.message}\n\n"
                            f"**温室**: {alert.greenhouse_id}\n"
                            f"**类型**: {alert.alert_type}\n"
                            f"**级别**: {alert.level}\n"
                            f"**时间**: {alert.created_at}",
                }
            }
        elif platform == "feishu":
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": f"{emoji} 智慧农业告警"},
                    },
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": alert.message}},
                        {"tag": "div", "text": {"tag": "lark_md", "content": f"**温室**: {alert.greenhouse_id}"}},
                        {"tag": "div", "text": {"tag": "lark_md", "content": f"**类型**: {alert.alert_type}"}},
                    ]
                }
            }
        else:
            return

        # 异步发送 HTTP POST
        asyncio.create_task(self._http_post(url, payload))

    async def _http_post(self, url: str, payload: dict):
        """异步 HTTP POST（Webhook 通知）"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    print(f"✅ Webhook sent to {url[:50]}...")
                else:
                    print(f"⚠️ Webhook failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Webhook error: {e}")

    async def _get_webhook_config(self, tenant_id: UUID) -> Optional[dict]:
        """获取租户的 Webhook 配置（从数据库或缓存）"""
        if tenant_id in self._webhook_cache:
            return self._webhook_cache[tenant_id]

        # TODO: 从数据库读取租户 webhook 配置
        # 目前返回 None（无 webhook 配置）
        return None

    def register_webhook(self, tenant_id: str, url: str, platform: str = "dingtalk"):
        """注册钉钉/飞书 Webhook（管理 API 调用）"""
        self._webhook_cache[UUID(tenant_id)] = {"url": url, "platform": platform}


# 全局单例
alert_notification_service: Optional[AlertNotificationService] = None


def get_alert_notification_service() -> AlertNotificationService:
    global alert_notification_service
    if alert_notification_service is None:
        alert_notification_service = AlertNotificationService()
    return alert_notification_service
