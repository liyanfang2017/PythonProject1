"""
场景2：日志 / 行为事件收集 —— 用户点击、页面埋点事件批量落库

业务流程：
  1. 前端/客户端上报用户行为事件（点击、页面浏览、停留时长）
  2. 生产者快速写入 Redis Streams（不阻塞上报接口）
  3. 消费者批量拉取事件，攒够一批后统一写入文件/数据库
  4. 批量写入比逐条写入性能高几个数量级

核心价值：高并发埋点场景下，Streams 削峰填谷，消费者批量落库降低 DB 压力。

运行方式（需要先启动 Redis）：
  # 终端A：启动消费者（批量落库）
  python scenario2_log_collection.py consumer

  # 终端B：模拟用户行为事件上报（连续产生 20 条）
  python scenario2_log_collection.py producer
"""

import asyncio
import json
import random
import sys
import time

import redis.asyncio as redis

STREAM_NAME = "user_event_stream"
GROUP_NAME = "user_event_group"
LOG_FILE = "./user_events.log"  # 模拟数据库，实际项目写入 ClickHouse / ES

# 批量落库阈值：攒够 5 条或等待超过 3 秒就刷一次
BATCH_SIZE = 5
BATCH_TIMEOUT = 3.0


# ---------------------------------------------------------------------------
# 生产者：模拟前端上报用户行为事件
# ---------------------------------------------------------------------------
async def producer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    events = ["page_view", "click", "scroll", "add_to_cart", "search", "share"]
    pages = ["/home", "/product/123", "/cart", "/checkout", "/profile", "/search?q=phone"]

    print("[生产者] 开始模拟用户行为事件上报（20条）...\n")

    for i in range(20):
        event = {
            "event_id": f"evt_{int(time.time() * 1000)}_{i}",
            "user_id": f"u{random.randint(1000, 9999)}",
            "event_type": random.choice(events),
            "page": random.choice(pages),
            "timestamp": int(time.time()),
            "device": random.choice(["ios", "android", "web"]),
        }

        msg_id = await client.xadd(
            STREAM_NAME,
            {"event_data": json.dumps(event, ensure_ascii=False)},
        )
        print(f"  [{i+1}/20] 上报 {event['event_type']} @ {event['page']}  msg_id={msg_id}")

        # 模拟事件上报间隔（实际中是毫秒级高频）
        await asyncio.sleep(0.1)

    print("\n[生产者] 20 条事件全部上报完成")
    await client.close()


# ---------------------------------------------------------------------------
# 消费者：批量拉取事件，攒批后统一写入文件（模拟数据库）
# ---------------------------------------------------------------------------
async def consumer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    try:
        await client.xgroup_create(STREAM_NAME, GROUP_NAME, mkstream=True)
    except Exception:
        pass

    print(f"[消费者] 启动，批量落库模式（每 {BATCH_SIZE} 条或 {BATCH_TIMEOUT}s 刷一次）")
    print(f"[消费者] 落库目标文件: {LOG_FILE}\n")

    batch = []  # 当前批次缓存
    last_flush = time.time()

    while True:
        # 拉取一批消息（count 控制最多拉多少条）
        res = await client.xreadgroup(
            groupname=GROUP_NAME,
            consumername="consumer-1",
            streams={STREAM_NAME: ">"},
            count=BATCH_SIZE,
            block=2000,
        )

        if res:
            for stream_name, msg_list in res:
                for msg_id, payload in msg_list:
                    event = json.loads(payload["event_data"])
                    batch.append((msg_id, event))
                    print(f"  [缓存] {event['event_type']} - {event['user_id']} (当前批次 {len(batch)}/{BATCH_SIZE})")

        # 判断是否需要刷盘：攒够一批 或 超时
        now = time.time()
        if len(batch) >= BATCH_SIZE or (batch and (now - last_flush) >= BATCH_TIMEOUT):
            # 批量写入文件（模拟批量 INSERT 到数据库）
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                for msg_id, event in batch:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")

            # 批量 ACK 所有消息
            msg_ids = [mid for mid, _ in batch]
            await client.xack(STREAM_NAME, GROUP_NAME, *msg_ids)

            print(f"\n  ✅ 批量落库 {len(batch)} 条，ACK 完成，已写入 {LOG_FILE}\n")

            batch.clear()
            last_flush = now


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scenario2_log_collection.py producer   # 模拟事件上报")
        print("  python scenario2_log_collection.py consumer   # 启动批量落库消费者")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "producer":
        asyncio.run(producer())
    elif mode == "consumer":
        asyncio.run(consumer())
    else:
        print(f"无效参数: {mode}")
        sys.exit(1)
