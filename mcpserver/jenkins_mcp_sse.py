from mcp.server.fastmcp import FastMCP
import uvicorn
import requests
import os
from pathlib import Path

# 启动时自动加载项目根目录 .env（无论以何种方式启动都生效）
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

# ========== 配置（服务器环境变量读取，不要硬编码） ==========
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

app = FastMCP("jenkins-mcp-sse")


@app.tool()
async def get_jenkins_job_status(job_name: str) -> str:
    """查询Jenkins任务最新构建状态

    Args:
        job_name: jenkins job名称
    """
    url = f"{JENKINS_URL}/job/{job_name}/lastBuild/api/json"
    resp = requests.get(url, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=10)
    if resp.status_code != 200:
        return f"请求失败 code={resp.status_code}, msg={resp.text}"
    data = resp.json()
    return (
        f"Job:{job_name}\n"
        f"构建编号:{data['number']}\n"
        f"状态:{data['result']}\n"
        f"构建时间:{data['timestamp']}\n"
        f"构建URL:{data['url']}"
    )


if __name__ == "__main__":
    starlette_app = app.sse_app()  # 默认路由: /sse + /messages/
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)
