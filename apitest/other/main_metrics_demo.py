from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Counter, CollectorRegistry

# 单独使用私有Registry，不碰prometheus_client全局REGISTRY
# reload=True时spawn子进程会把本模块执行两次，只有全程使用私有Registry才不会DuplicateTimeseries
CUSTOM_REGISTRY = CollectorRegistry(auto_describe=False)

# -------- 自定义业务计数器，注册到私有Registry，不走全局 --------
WEBHOOK_SIGN_VERIFY_FAILED = Counter(
    "webhook_sign_verify_failed_total",
    "webhook签名校验失败总次数",
    registry=CUSTOM_REGISTRY
)

app = FastAPI(title="Prometheus‑FastAPI‑Instrumentator Demo")

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=False,
    should_respect_env_var=False,
    env_var_name="ENABLE_METRICS",
    excluded_handlers=["/health"],
    registry=CUSTOM_REGISTRY,
)

instrumentator.add(metrics.request_size())
instrumentator.add(metrics.response_size())
instrumentator.add(metrics.latency())

instrumentator.instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/success")
def api_success():
    return {"msg": "success response"}


@app.get("/api/fake_403")
def api_fake_403():
    WEBHOOK_SIGN_VERIFY_FAILED.inc()
    raise HTTPException(status_code=403, detail="签名校验失败")


@app.get("/api/fake_500")
def api_fake_500():
    raise HTTPException(status_code=500, detail="内部服务错误")


if __name__ == "__main__":
    import uvicorn
    # reload=True可用：指标全程注册在私有Registry，双重导入不冲突
    uvicorn.run("main_metrics_demo:app", host="127.0.0.1", port=8003, reload=True)
