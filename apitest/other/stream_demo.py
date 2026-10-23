from fastapi import FastAPI
from starlette.responses import StreamingResponse
import asyncio

app = FastAPI(title="StreamingResponse SSE & CSV流式导出Demo")


# ================= Demo1 SSE 服务器单向推送 =================
async def sse_generator():
    """SSE事件异步生成器，遵循SSE协议格式 data:xxx\n\n"""
    for i in range(10):
        yield f"data: {i} 号推送消息\n\n"
        await asyncio.sleep(1)


@app.get("/sse")
async def sse_endpoint():
    """SSE实时推送接口，浏览器直接访问"""
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream"
    )


# ================= Demo2 CSV大文件流式导出 =================
def csv_stream():
    """同步生成器，逐行产出csv，不会一次性把全部数据加载进内存"""
    yield "id,name,age\n"
    # 模拟海量数据，这里10000行，可以改成百万行，内存不会暴涨
    for row_id in range(100):
        yield f"{row_id},user_{row_id},{20 + row_id % 10}\n"


@app.get("/export_csv")
async def export_csv():
    """流式下载CSV，浏览器直接触发文件下载"""
    return StreamingResponse(
        csv_stream(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="data.csv"'}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("stream_demo:app", host="127.0.0.1", port=8001, reload=True)
