# demo_redis_pubsub_sub.py
# Pub/Sub 订阅者示例（单独脚本运行，阻塞等待消息）
# 缺陷：订阅者断开期间发布的消息直接丢失，**不适合业务消息队列，仅适合通知广播**。
import asyncio
import redis.asyncio as redis

async def main():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe("sys_notice")
    print("等待广播消息...")
    async for msg in pubsub.listen():
        if msg["type"] == "message":
            print(f"[PubSub收到] {msg['data']}")

if __name__ == "__main__":
    asyncio.run(main())
