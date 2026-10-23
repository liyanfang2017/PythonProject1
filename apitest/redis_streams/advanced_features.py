"""
高级特性合集：Pending 恢复 + MAXLEN + 多消费者并发 + 删除历史消息

本 demo 覆盖 Redis Streams 生产环境必备的 4 个高级能力：

  1. MAXLEN —— xadd 时限制流最大长度，防止消息无限堆积占满 Redis 内存
  2. 多消费者并发 —— 同一个消费组下 consumer-1/2/3 分担消息，提升吞吐量
  3. Pending 恢复 —— 消费者崩溃未 ACK 的消息进入 pending，重启后 xclaim 重新处理
  4. 删除历史消息 —— 已处理完毕的消息用 xdel 删除，释放内存

运行方式（需要先启动 Redis）：

  # ① 查看当前流状态
  python advanced_features.py status

  # ② 生产消息（带 MAXLEN=5，超过5条自动裁剪旧消息）
  python advanced_features.py producer

  # ③ 启动多个消费者（开3个终端，分别运行，观察消息分担）
  python advanced_features.py consumer 1
  python advanced_features.py consumer 2
  python advanced_features.py consumer 3

  # ④ 模拟消费者崩溃（读一条消息不 ACK 就退出，消息进入 pending）
  python advanced_features.py crash

  # ⑤ 故障恢复：扫描 pending 消息，xclaim 接管并重新处理
  python advanced_features.py recover

  # ⑥ 删除已处理完毕的历史消息
  python advanced_features.py cleanup
"""

import asyncio
import json
import sys
import time

import redis.asyncio as redis

STREAM_NAME = "advanced_stream"
GROUP_NAME = "advanced_group"
MAXLEN = 5  # 流最大保留消息数（演示用，生产环境一般设几万）


# ---------------------------------------------------------------------------
# 工具：确保消费组存在
# ---------------------------------------------------------------------------
async def ensure_group(client):
    try:
        await client.xgroup_create(STREAM_NAME, GROUP_NAME, mkstream=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1. 生产者：带 MAXLEN 限制流长度
# ---------------------------------------------------------------------------
async def producer():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    await ensure_group(client)

    print(f"[生产者] 开始写入 10 条消息，MAXLEN={MAXLEN}（超过自动裁剪旧消息）\n")

    for i in range(10):
        msg_id = await client.xadd(
            STREAM_NAME,
            {"task_id": f"task_{i}", "data": f"消息内容_{i}"},
            maxlen=MAXLEN,        # 限制流最大长度
            approximate=True,      # 近似裁剪，性能更好（几乎精确）
        )
        length = await client.xlen(STREAM_NAME)
        print(f"  [{i+1}/10] 写入 msg_id={msg_id}, 当前流长度={length}")
        await asyncio.sleep(0.1)

    print(f"\n[生产者] 完成。流最终长度={await client.xlen(STREAM_NAME)}（被 MAXLEN 裁剪到 {MAXLEN}）")
    await client.close()


# ---------------------------------------------------------------------------
# 2. 多消费者：同一个消费组下多个消费者分担消息
# ---------------------------------------------------------------------------
async def consumer(consumer_id: str):
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    await ensure_group(client)

    name = f"consumer-{consumer_id}"
    print(f"[{name}] 启动，加入消费组 {GROUP_NAME}")
    print(f"[{name}] 同组其他消费者会和我分担消息，每条消息只会被一个消费者处理\n")

    while True:
        res = await client.xreadgroup(
            groupname=GROUP_NAME,
            consumername=name,
            streams={STREAM_NAME: ">"},   # ">" 只拿新消息
            block=3000,
            count=1,                        # 每次拿1条，便于观察分担效果
        )

        if not res:
            continue

        for stream_name, msg_list in res:
            for msg_id, payload in msg_list:
                print(f"[{name}] 处理 msg_id={msg_id}, task_id={payload['task_id']}")
                await asyncio.sleep(0.3)  # 模拟业务处理耗时
                await client.xack(STREAM_NAME, GROUP_NAME, msg_id)
                print(f"[{name}] ✅ ACK 完成 msg_id={msg_id}\n")


# ---------------------------------------------------------------------------
# 3. 模拟崩溃：读取消息但不 ACK，直接退出 → 消息进入 pending
# ---------------------------------------------------------------------------
async def crash():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    await ensure_group(client)

    print("[崩溃模拟] 读取一条消息，但故意不 ACK，模拟进程崩溃...\n")

    res = await client.xreadgroup(
        groupname=GROUP_NAME,
        consumername="crashed-consumer",
        streams={STREAM_NAME: ">"},
        block=2000,
        count=1,
    )

    if not res:
        print("[崩溃模拟] 没有新消息可读，请先运行 producer")
        await client.close()
        return

    for stream_name, msg_list in res:
        for msg_id, payload in msg_list:
            print(f"[崩溃模拟] 读取到 msg_id={msg_id}, task_id={payload['task_id']}")
            print(f"[崩溃模拟] 正在处理... 突然崩溃！没有执行 ACK！")
            print(f"[崩溃模拟] 进程退出，这条消息将停留在 pending 列表中\n")

    # 故意不调用 xack，直接关闭连接退出
    await client.close()

    # 查看 pending 状态
    client2 = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    pending = await client2.xpending(STREAM_NAME, GROUP_NAME)
    print(f"[崩溃模拟] 当前 pending 消息数: {pending['pending']}")
    print(f"[崩溃模拟] pending 消息 ID 范围: {pending['min']} ~ {pending['max']}")
    await client2.close()


# ---------------------------------------------------------------------------
# 4. 故障恢复：扫描 pending，xclaim 接管，重新处理并 ACK
# ---------------------------------------------------------------------------
async def recover():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    await ensure_group(client)

    print("[故障恢复] 扫描 pending 列表中未 ACK 的消息...\n")

    # 第一步：查看 pending 概况
    pending_info = await client.xpending(STREAM_NAME, GROUP_NAME)
    print(f"[故障恢复] pending 总数: {pending_info['pending']}")
    print(f"[故障恢复] pending 范围: {pending_info['min']} ~ {pending_info['max']}")

    if pending_info["pending"] == 0:
        print("\n[故障恢复] 没有 pending 消息，无需恢复")
        await client.close()
        return

    # 第二步：获取 pending 消息详情（每条消息被哪个消费者领取、空闲多久）
    pending_details = await client.xpending_range(
        STREAM_NAME,
        GROUP_NAME,
        min="-",
        max="+",
        count=10,
    )
    print(f"\n[故障恢复] pending 消息详情:")
    for p in pending_details:
        print(f"  msg_id={p['message_id']}, consumer={p['consumer']}, "
              f"空闲时间={p['time_since_delivered']}ms, 投递次数={p['times_delivered']}")

    # 第三步：xclaim 接管所有 pending 消息（转移给当前消费者）
    msg_ids = [p["message_id"] for p in pending_details]
    print(f"\n[故障恢复] 执行 xclaim，接管 {len(msg_ids)} 条 pending 消息...")

    claimed = await client.xclaim(
        STREAM_NAME,
        GROUP_NAME,
        "recover-consumer",
        min_idle_time=0,       # 空闲超过0ms就接管（演示用，生产一般设 30000ms）
        message_ids=msg_ids,
    )

    # 第四步：重新处理并 ACK
    for msg_id, payload in claimed:
        print(f"\n[故障恢复] 重新处理 msg_id={msg_id}, task_id={payload.get('task_id', 'N/A')}")
        await asyncio.sleep(0.2)  # 模拟重新执行业务逻辑
        await client.xack(STREAM_NAME, GROUP_NAME, msg_id)
        print(f"[故障恢复] ✅ 重新处理完成并 ACK, msg_id={msg_id}")

    # 验证 pending 已清空
    pending_after = await client.xpending(STREAM_NAME, GROUP_NAME)
    print(f"\n[故障恢复] 恢复后 pending 数: {pending_after['pending']}（应为 0）")
    await client.close()


# ---------------------------------------------------------------------------
# 5. 删除历史消息：已处理完毕的消息用 xdel 删除
# ---------------------------------------------------------------------------
async def cleanup():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    length_before = await client.xlen(STREAM_NAME)
    print(f"[清理] 删除前流长度: {length_before}")

    # 读取流中所有消息（实际生产中按时间范围删除，这里演示全删）
    all_msgs = await client.xrange(STREAM_NAME, min="-", max="+")

    if not all_msgs:
        print("[清理] 流中没有消息")
        await client.close()
        return

    # 检查哪些消息已经 ACK（不在 pending 中）
    pending_info = await client.xpending(STREAM_NAME, GROUP_NAME)
    pending_ids = set()
    if pending_info["pending"] > 0:
        details = await client.xpending_range(STREAM_NAME, GROUP_NAME, "-", "+", count=100)
        pending_ids = {p["message_id"] for p in details}

    # 只删除已 ACK 的消息，pending 中的不删（还没处理完）
    to_delete = [mid for mid, _ in all_msgs if mid not in pending_ids]
    print(f"[清理] 已 ACK 可删除消息数: {len(to_delete)}")
    print(f"[清理] pending 中不可删除消息数: {len(pending_ids)}")

    if to_delete:
        deleted = await client.xdel(STREAM_NAME, *to_delete)
        print(f"[清理] 实际删除消息数: {deleted}")

    length_after = await client.xlen(STREAM_NAME)
    print(f"[清理] 删除后流长度: {length_after}")
    await client.close()


# ---------------------------------------------------------------------------
# 6. 状态查看
# ---------------------------------------------------------------------------
async def status():
    client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

    exists = await client.exists(STREAM_NAME)
    if not exists:
        print("[状态] 流不存在，请先运行 producer")
        await client.close()
        return

    length = await client.xlen(STREAM_NAME)
    print(f"[状态] 流名称: {STREAM_NAME}")
    print(f"[状态] 流长度(消息数): {length}")

    # 消费组信息
    groups = await client.xinfo_groups(STREAM_NAME)
    print(f"\n[状态] 消费组数量: {len(groups)}")
    for g in groups:
        print(f"  组名: {g['name']}, 消费者数: {g['consumers']}, "
              f"pending: {g['pending']}, 最后投递ID: {g['last-delivered-id']}")

    # 最近3条消息
    recent = await client.xrevrange(STREAM_NAME, max="+", min="-", count=3)
    print(f"\n[状态] 最近3条消息:")
    for mid, payload in recent:
        print(f"  {mid}: {payload}")

    await client.aclose()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "producer":
        asyncio.run(producer())
    elif mode == "consumer":
        cid = sys.argv[2] if len(sys.argv) > 2 else "1"
        asyncio.run(consumer(cid))
    elif mode == "crash":
        asyncio.run(crash())
    elif mode == "recover":
        asyncio.run(recover())
    elif mode == "cleanup":
        asyncio.run(cleanup())
    elif mode == "status":
        asyncio.run(status())
    else:
        print(f"无效参数: {mode}")
        print(__doc__)
        sys.exit(1)
