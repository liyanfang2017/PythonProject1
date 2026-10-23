# demo_rabbitmq.py
### 3. RabbitMQ（aio‑pika 异步）
# 特点：交换机、队列、死信队列、重试、灵活路由；传统业务 MQ，可靠性强。
# > 需要本地启动 RabbitMQ 服务。
# python demo_rabbitmq.py producer
# python demo_rabbitmq.py consumer
# 特点：支持死信队列、延迟消息、多种交换机 (fanout/direct/topic)，业务系统任务队列首选。
import asyncio
import aio_pika

async def producer():
    connection = await aio_pika.connect_robust("amqp://guest:guest@127.0.0.1/")
    channel = await connection.channel()
    # 声明队列
    queue = await channel.declare_queue("order_queue", durable=True)
    msg_body = '{"order_id":"ord_002","user_id":"u1002"}'
    await channel.default_exchange.publish(
        aio_pika.Message(body=msg_body.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=queue.name
    )
    print("[RabbitMQ生产者]消息发送完成")
    await connection.close()

async def consumer():
    connection = await aio_pika.connect_robust("amqp://guest:guest@127.0.0.1/")
    channel = await connection.channel()
    # 消息确认关闭自动ack，手动ack/nack
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue("order_queue", durable=True)

    async def callback(msg: aio_pika.IncomingMessage):
        async with msg.process():
            print(f"[RabbitMQ消费] {msg.body.decode()}")
            # 业务处理完成自动ack；异常抛出则nack重新入队

    await queue.consume(callback)
    print("[RabbitMQ消费者启动")
    await asyncio.Future() #永久阻塞

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "producer":
        asyncio.run(producer())
    elif sys.argv[1] == "consumer":
        asyncio.run(consumer())
