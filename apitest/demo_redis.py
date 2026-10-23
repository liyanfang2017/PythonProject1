# demo_redis.py
#Redis 异步（redis‑py asyncio）
# 能力演示：缓存、幂等键、refresh_token 黑名单、Pub/Sub 广播

import asyncio
import redis.asyncio as redis



async def main():
    client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

    # 1.缓存：设置热点数据，60秒过期
    await client.setex("cache:pet:10", 2, '{"name":"doggie"}')

    val = await client.get("cache:pet:10")
    print("[缓存读取1]", val)
    await asyncio.sleep(2)
    val = await client.get("cache:pet:10")
    print("[缓存读取2]", val)

    # 2.幂等键 set nx：防止重复提交
    idemp_key = "idemp:req_abc123"
    ok = await client.set(idemp_key, "1", ex=300, nx=True)
    if ok:
        print("[幂等]第一次请求，执行业务")
    else:
        print("[幂等]重复请求，拒绝")

    # 3.refresh_token 撤销黑名单
    rt = "refresh_token_xxxx"
    await client.setex(f"revoke:{rt}", 86400, "1")
    is_revoke = await client.exists(f"revoke:{rt}")
    print("[token已作废]", bool(is_revoke))

    # 4.Pub/Sub 发布广播
    await client.publish("sys_notice", "有新订单产生")
    print("[PubSub]发送广播消息")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
