"""
RabbitMQ 连接模块
RabbitMQ Connection Module
"""

import aio_pika
from aio_pika import ExchangeType
from app.core.config import settings

amqp_connection: aio_pika.RobustConnection = None
amqp_channel: aio_pika.Channel = None

# 告警广播用的 fanout exchange
alert_exchange: aio_pika.Exchange = None


async def init_rabbitmq():
    global amqp_connection, amqp_channel, alert_exchange

    amqp_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    amqp_channel = await amqp_connection.channel()

    # 声明告警广播 fanout exchange
    alert_exchange = await amqp_channel.declare_exchange(
        "alerts.fanout",
        ExchangeType.FANOUT,
        durable=True,
    )

    return amqp_channel


async def close_rabbitmq():
    global amqp_connection
    if amqp_connection:
        await amqp_connection.close()


def get_rabbitmq_channel() -> aio_pika.Channel:
    return amqp_channel


def get_alert_exchange() -> aio_pika.Exchange:
    return alert_exchange
