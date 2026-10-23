"""
场景3：分布式服务事件通知 —— 一个事件，多个服务独立消费

业务流程：
  1. 用户服务（Service A）用户注册成功，发出 "user_registered" 事件
  2. 邮件服务（Service B）作为独立消费组，消费事件 → 发送欢迎邮件
  3. 画像服务（Service C）作为独立消费组，消费事件 → 初始化用户画像

核心概念：
  - 同一个 Stream，多个**不同的消费组**，每个消费组独立消费全部消息
  - Service B 和 Service C 互不干扰，各自有独立的消费进度
  - 这和"同一个消费组下多个消费者分担消息"完全不同

运行方式（需要先启动 Redis）：
  # 终端A：启动邮件服务消费者（消费组 email_group）
  python scenario3_service_event.py consumer email

  # 终端B：启动画像服务消费者（消费组 profile_group）
  python scenario3_service_event.py consumer profile

  # 终端C：模拟用户服务发布注册事件
  python scenario3_service_event.py producer

  观察：两个消费者都会收到同一条注册事件，各自处理。
"""

import asyncio
import json
import sys
import time

import redis.asyncio as redis

STREAM_NAME = "user_event_bus"

# 两个独立的消费组，对应两个微服务
GROUP_EMAIL = "email_service_group"    # 邮件服务
GROUP_PROFILE = "profile_service_group"  # 画像服务


# ---------------------------------------------------------------------------
# 生产者：模拟用户服务（Service A）发布注册事件
# ---------------------------------------------------------------------------
async def producer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    user = {
        "user_id": f"u{int(time.time())}",
        "username": "新用户小明",
        "email": "xiaoming@example.com",
        "register_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    print(f"[用户服务] 用户注册成功: {user['username']} ({user['user_id']})")

    # 发布事件到 Stream（只写一次，所有消费组都能收到）
    msg_id = await client.xadd(
        STREAM_NAME,
        {
            "event_type": "user_registered",
            "payload": json.dumps(user, ensure_ascii=False),
        },
    )
    print(f"[用户服务] 事件已发布到事件总线, msg_id={msg_id}")
    print(f"[用户服务] 邮件服务和画像服务将各自独立消费此事件\n")

    await client.close()


# ---------------------------------------------------------------------------
# 消费者：根据参数启动不同服务的消费组
# ---------------------------------------------------------------------------
async def consumer(service_name: str):
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    if service_name == "email":
        group = GROUP_EMAIL
        consumer_name = "email-consumer-1"
        print("[邮件服务] 启动，消费组: email_service_group\n")
    elif service_name == "profile":
        group = GROUP_PROFILE
        consumer_name = "profile-consumer-1"
        print("[画像服务] 启动，消费组: profile_service_group\n")
    else:
        print(f"未知服务: {service_name}")
        return

    # 每个服务创建自己的消费组（互相独立）
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
                event_type = payload["event_type"]

                if service_name == "email":
                    # ---- 邮件服务逻辑 ----
                    print(f"[邮件服务] 收到事件 {event_type}, msg_id={msg_id}")
                    print(f"  → 向 {event['email']} 发送欢迎邮件...")
                    await asyncio.sleep(0.3)
                    print(f"  ✅ 欢迎邮件发送完成\n")

                elif service_name == "profile":
                    # ---- 画像服务逻辑 ----
                    print(f"[画像服务] 收到事件 {event_type}, msg_id={msg_id}")
                    print(f"  → 为用户 {event['user_id']} 初始化画像数据...")
                    await asyncio.sleep(0.5)
                    print(f"  ✅ 用户画像初始化完成\n")

                # 各自独立 ACK（不影响另一个消费组的消费进度）
                await client.xack(STREAM_NAME, group, msg_id)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scenario3_service_event.py producer            # 发布用户注册事件")
        print("  python scenario3_service_event.py consumer email      # 启动邮件服务消费者")
        print("  python scenario3_service_event.py consumer profile    # 启动画像服务消费者")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "producer":
        asyncio.run(producer())
    elif mode == "consumer":
        if len(sys.argv) < 3:
            print("请指定服务: email 或 profile")
            sys.exit(1)
        asyncio.run(consumer(sys.argv[2]))
    else:
        print(f"无效参数: {mode}")
        sys.exit(1)
