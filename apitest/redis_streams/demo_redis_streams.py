# demo_redis_streams.py
#  Redis Streams（Redis 内置可靠消息队列，消费组 + ACK）
# 核心特性：消息持久存储、消费组、消息 ACK 确认、pending 未确认消息，无需部署额外中间件。
# # 生产消息
# python demo_redis_streams.py producer
# # 启动消费者（另一个终端）
# python demo_redis_streams.py consumer

import asyncio
import redis.asyncio as redis

STREAM_NAME = "order_stream"
GROUP_NAME = "order_consumer_group"

async def producer():
    """生产者：写入消息到streams"""
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    msg_id = await client.xadd(
        STREAM_NAME,
        {"order_id": "ord_001", "user_id": "u1001", "action": "create"}
    )
    print(f"[Streams生产者]写入消息id:{msg_id}")
    await client.close()

async def consumer():
    """消费组消费者，必须ack，防止丢消息"""
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    # 初始化消费组（仅第一次运行执行）
    try:
        await client.xgroup_create(STREAM_NAME, GROUP_NAME, mkstream=True)
    except Exception:
        pass

    print("[Streams消费者启动，等待消息...")
    while True:
        # > 读取组内新消息，block阻塞等待
        res = await client.xreadgroup(
            groupname=GROUP_NAME,
            consumername="consumer‑1",
            streams={STREAM_NAME: ">"},
            block=3000
        )
        if not res:
            continue
        for stream, msg_list in res:
            for msg_id, payload in msg_list:
                print(f"[收到消息] id={msg_id}, data={payload}")
                # 模拟业务处理
                # 处理成功，ack确认；如果进程崩溃未ack，消息会进入pending可重新消费
                await client.xack(STREAM_NAME, GROUP_NAME, msg_id)
                print(f"[ack完成] {msg_id}")

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "producer":
        asyncio.run(producer())
    elif sys.argv[1] == "consumer":
        asyncio.run(consumer())
