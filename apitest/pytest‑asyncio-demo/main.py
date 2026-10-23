from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Counter, CollectorRegistry


class Settings(BaseSettings):
    # 默认配置，可被操作系统环境变量覆盖，不再读取独立.env文件
    app_name: str = "demo_app"
    debug: bool = True
    port: int = 8003
    prometheus_enable: bool = True

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


settings = Settings()

# prometheus自定义业务指标
CUSTOM_REGISTRY = CollectorRegistry(auto_describe=False)
WEBHOOK_SIGN_FAIL_TOTAL = Counter(
    "webhook_sign_verify_failed_total",
    "webhook签名校验失败总次数",
    registry=CUSTOM_REGISTRY
)

instrumentator = Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/health"],
    registry=CUSTOM_REGISTRY,
)
instrumentator.add(metrics.request_size())
instrumentator.add(metrics.response_size())
instrumentator.add(metrics.latency())


app = FastAPI(title=settings.app_name, debug=settings.debug)

# /metrics 在模块导入时注册，而非lifespan中：
# httpx的ASGITransport发起测试请求不会执行lifespan，放lifespan里测试拿不到该路由
if settings.prometheus_enable:
    instrumentator.instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/hello")
async def hello():
    return {"msg": "hello world"}


@app.post("/api/add")
async def add(a: int, b: int):
    return {"sum": a + b}


@app.get("/api/webhook_fail")
async def webhook_fail():
    WEBHOOK_SIGN_FAIL_TOTAL.inc()
    raise HTTPException(status_code=403, detail="signature verify failed")


@app.get("/api/fake_500")
async def fake_500():
    raise HTTPException(status_code=500, detail="internal error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=settings.port, reload=settings.debug)
