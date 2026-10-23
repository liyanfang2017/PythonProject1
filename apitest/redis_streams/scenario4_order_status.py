"""
场景4：订单状态变更事件 —— 状态流转驱动多个下游系统

业务流程：
  1. 订单经历状态流转：created(已创建) → paid(已支付) → shipped(已发货) → completed(已完成)
  2. 每次状态变更，发布一条事件到 Streams
  3. 库存服务（消费组 inventory_group）：只在 paid 状态时扣减库存
  4. 通知服务（消费组 notify_group）：每个状态变更都通知用户

核心价值：订单服务不需要知道下游有哪些系统，只管发事件；
         下游系统各自订阅，按需处理，系统解耦。

运行方式（需要先启动 Redis）：
  # 终端A：启动库存服务消费者
  python scenario4_order_status.py consumer inventory

  # 终端B：启动通知服务消费者
  python scenario4_order_status.py consumer notify

  # 终端C：模拟订单状态流转（依次发布4个状态事件）
  python scenario4_order_status.py producer
"""

import asyncio
import json
import sys
import time

import redis.asyncio as redis

STREAM_NAME = "order_status_stream"
GROUP_INVENTORY = "inventory_service_group"  # 库存服务消费组
GROUP_NOTIFY = "notify_service_group"         # 通知服务消费组


# ---------------------------------------------------------------------------
# 生产者：模拟订单状态依次流转
# ---------------------------------------------------------------------------
async def producer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    order_id = f"ORD_{int(time.time())}"
    # 订单状态流转序列
    status_flow = [
        ("created", "订单已创建"),
        ("paid", "订单已支付"),
        ("shipped", "订单已发货"),
        ("completed", "订单已完成"),
    ]

    print(f"[订单服务] 订单 {order_id} 开始状态流转...\n")

    for status, desc in status_flow:
        event = {
            "order_id": order_id,
            "status": status,
            "desc": desc,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        msg_id = await client.xadd(
            STREAM_NAME,
            {
                "event_type": "order_status_changed",
                "payload": json.dumps(event, ensure_ascii=False),
            },
        )
        print(f"  [{status}] {desc}  → 事件已发布 msg_id={msg_id}")

        # 模拟状态之间的时间间隔
        await asyncio.sleep(0.5)

    print(f"\n[订单服务] 订单 {order_id} 状态流转完成")
    await client.close()


# ---------------------------------------------------------------------------
# 消费者：库存服务 / 通知服务
# ---------------------------------------------------------------------------
async def consumer(service_name: str):
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    if service_name == "inventory":
        group = GROUP_INVENTORY
        consumer_name = "inventory-consumer-1"
        print("[库存服务] 启动，消费组: inventory_service_group")
        print("[库存服务] 只处理 paid(已支付) 状态，扣减库存\n")
    elif service_name == "notify":
        group = GROUP_NOTIFY
        consumer_name = "notify-consumer-1"
        print("[通知服务] 启动，消费组: notify_service_group")
        print("[通知服务] 每个状态变更都通知用户\n")
    else:
        print(f"未知服务: {service_name}")
        return

    try:
        await client.xgroup_create(STREAM_NAME, group, mkstream=True)
    except Exception:
        pass

    while True:
        res = await client.xreadgroup(
            groupname=group,
            consumername=consumer_name,
            streams={STREAM_NAME: ">"},
            block=3000,
        )

        if not res:
            continue

        for stream_name, msg_list in res:
            for msg_id, payload in msg_list:
                event = json.loads(payload["payload"])
                status = event["status"]

                if service_name == "inventory":
                    # 库存服务：只在 paid 状态扣减库存，其他状态跳过
                    if status == "paid":
                        print(f"[库存服务] 订单 {event['order_id']} 已支付，扣减库存...")
                        await asyncio.sleep(0.3)
                        print(f"  ✅ 库存扣减完成\n")
                    else:
                        print(f"[库存服务] 状态 {status} 无需处理库存，跳过\n")

                elif service_name == "notify":
                    # 通知服务：每个状态都通知用户
                    print(f"[通知服务] 订单 {event['order_id']} 状态变更: {event['desc']}")
                    print(f"  → 向用户推送通知: 您的订单{event['desc']}")
                    await asyncio.sleep(0.2)
                    print(f"  ✅ 通知推送完成\n")

                await client.xack(STREAM_NAME, group, msg_id)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scenario4_order_status.py producer            # 模拟订单状态流转")
        print("  python scenario4_order_status.py consumer inventory  # 启动库存服务消费者")
        print("  python scenario4_order_status.py consumer notify     # 启动通知服务消费者")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "producer":
        asyncio.run(producer())
    elif mode == "consumer":
        if len(sys.argv) < 3:
            print("请指定服务: inventory 或 notify")
            sys.exit(1)
        asyncio.run(consumer(sys.argv[2]))
    else:
        print(f"无效参数: {mode}")
        sys.exit(1)
