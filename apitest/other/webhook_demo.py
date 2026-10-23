from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import requests
import json

app = FastAPI(title="Webhook HMAC-SHA256签名校验Demo")
# webhook密钥，双方必须保持完全一致，生产环境放到环境变量
WEBHOOK_SECRET = b"my-webhook-secret-key"


def verify_webhook_signature(raw_body: bytes, header_sign: str, secret: bytes) -> bool:
    computed_sign = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    # 强制过滤，只保留ASCII字符，消除非ASCII特殊符号
    safe_header_sign = ''.join(c for c in header_sign if c.isascii())
    return hmac.compare_digest(computed_sign, safe_header_sign)


@app.post("/webhook/receive")
async def webhook_receive(request: Request):
    raw_body = await request.body()
    header_sign = request.headers.get("X-Webhook-Signature", "")

    # --------调试打印----------
    print(f"【调试】raw_body字节: {raw_body}")
    local_calc_sign = hmac.new(WEBHOOK_SECRET, raw_body, hashlib.sha256).hexdigest()
    print(f"【调试】服务端本地计算签名: {local_calc_sign}")
    print(f"【调试】Header收到X-Webhook-Signature: {repr(header_sign)}")
    # -------------------------

    if not verify_webhook_signature(raw_body, header_sign, WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="签名校验失败，拒绝请求")

    payload = await request.json()
    print(f"✅成功收到webhook回调数据：{payload}")
    return {"ok": True, "msg": "webhook接收成功"}


def calc_sign_only():
    """只计算并打印签名，不发送http请求，复制输出到curl即可"""
    payload = {"event": "order_pay", "order_id": 10086, "status": "success"}
    body_bytes = json.dumps(payload).encode("utf-8")
    sign = hmac.new(WEBHOOK_SECRET, body_bytes, hashlib.sha256).hexdigest()
    print("\n========== 给curl使用的签名 ==========")
    print(f"X-Webhook-Signature 的值：\n{sign}")
    print("\n可直接复制完整curl命令：")
    curl_text = f'''curl -X POST http://127.0.0.1:8002/webhook/receive \\
-H "Content-Type: application/json" \\
-H "X-Webhook-Signature: {sign}" \\
-d '{{"event":"order_pay","order_id":10086,"status":"success"}}' '''
    print(curl_text)
    print("======================================\n")
    return sign


def mock_third_party_send_webhook():
    """模拟第三方平台：生成签名，发起webhook回调（测试用）"""
    url = "http://127.0.0.1:8002/webhook/receive"
    payload = {"event": "order_pay", "order_id": 10086, "status": "success"}
    body_bytes = json.dumps(payload).encode("utf-8")

    # 第三方计算HMAC‑SHA256签名
    sign = hmac.new(WEBHOOK_SECRET, body_bytes, hashlib.sha256).hexdigest()
    print(f"\n【mock函数生成签名】X-Webhook-Signature={sign}\n")

    headers = {
        "X-Webhook-Signature": sign,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, data=body_bytes, headers=headers)
    print(f"模拟第三方调用结果 status={resp.status_code}, resp={resp.text}")


if __name__ == "__main__":
    # 在启动服务前，可以直接打印签名
    calc_sign_only()

    import uvicorn
    uvicorn.run("webhook_demo:app", host="127.0.0.1", port=8002, reload=True)
