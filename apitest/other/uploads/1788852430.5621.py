"""
场景1：接口异步任务解耦 —— 下单后发短信/生成报表不阻塞接口响应

业务流程：
  1. 用户调用下单接口（producer 模拟）
  2. 接口只做：创建订单 + 写入 Redis Streams，立刻返回"下单成功"
  3. 后台消费者进程独立运行，从 Streams 读取订单事件
  4. 消费者执行慢操作：发短信、推送通知、生成对账单

核心价值：前端不用等待慢 IO，接口响应从 3 秒降到 50ms；
         消费者崩溃时消息进入 pending，重启后可重新处理，不丢消息。

运行方式（需要先启动 Redis）：
  # 终端A：启动消费者（后台常驻）
  python scenario1_async_task.py consumer

  # 终端B：模拟下单（生产者）
  python scenario1_async_task.py producer
"""

import asyncio
import json
import sys
import time

import redis.asyncio as redis

STREAM_NAME = "order_task_stream"
GROUP_NAME = "order_task_group"


# ---------------------------------------------------------------------------
# 生产者：模拟"下单接口"
# ---------------------------------------------------------------------------
async def producer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    # 模拟一条订单数据（实际业务中来自 HTTP 请求体）
    order = {
        "order_id": f"ORD_{int(time.time() * 1000)}",
        "user_id": "u1001",
        "goods": "机械键盘",
        "amount": 399.00,
    }

    print(f"[下单接口] 收到订单: {order['order_id']}")

    # ---- 接口内只做两件事：1) 模拟落库  2) 写消息队列 ----
    # （真实项目中这里是 SQLAlchemy 异步写数据库）
    await asyncio.sleep(0.05)  # 模拟数据库写入耗时

    # 把订单事件写入 Streams，复杂对象用 json.dumps 序列化成字符串
    msg_id = await client.xadd(
        STREAM_NAME,
        {
            "event_type": "order_created",
            "order_data": json.dumps(order, ensure_ascii=False),
        },
    )
    print(f"[下单接口] 消息已写入 Streams, msg_id={msg_id}")
    print(f"[下单接口] 立即返回前端: 下单成功 (耗时约 50ms)")

    await client.aclose()


# ---------------------------------------------------------------------------
# 消费者：后台独立进程，执行慢任务
# ---------------------------------------------------------------------------
async def consumer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    # 创建消费组（仅第一次有效，已存在会报错，忽略即可）
    try:
        await client.xgroup_create(STREAM_NAME, GROUP_NAME, mkstream=True)
    except Exception:
        pass

    print("[消费者] 启动，等待订单事件...\n")

    while True:
        # ">" 表示只读取本消费组尚未消费过的新消息
        # block=5000 表示没有消息时阻塞等待 5 秒，避免空转耗 CPU
        res = await client.xreadgroup(
            groupname=GROUP_NAME,
            consumername="consumer-1",
            streams={STREAM_NAME: ">"},
            block=5000,
        )

        if not res:
            continue

        for stream_name, msg_list in res:
            for msg_id, payload in msg_list:
                # 反序列化订单数据
                order = json.loads(payload["order_data"])
                print(f"[消费者] 收到订单事件: {order['order_id']}")

                # ---- 模拟执行多个慢任务（这些在接口里同步做会拖慢响应）----
                print(f"  → 发送短信通知用户 {order['user_id']}...")
                await asyncio.sleep(0.5)  # 模拟调用短信网关

                print(f"  → 推送 App 通知...")
                await asyncio.sleep(0.3)  # 模拟推送服务

                print(f"  → 生成对账单 PDF...")
                await asyncio.sleep(1.0)  # 模拟报表生成

                # 全部处理成功后，ACK 确认
                await client.xack(STREAM_NAME, GROUP_NAME, msg_id)
                print(f"  ✅ 全部任务完成, ACK 确认 msg_id={msg_id}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scenario1_async_task.py producer   # 模拟下单")
        print("  python scenario1_async_task.py consumer   # 启动后台消费者")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "producer":
        asyncio.run(producer())
    elif mode == "consumer":
        asyncio.run(consumer())
    else:
        print(f"无效参数: {mode}")
        sys.exit(1)
