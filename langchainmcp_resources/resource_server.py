"""
MCP Server 示例：对外暴露 Resources 只读资源
mcp 1.x FastMCP
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resource‑demo‑server")


# 静态文本资源，固定URI
@mcp.resource("info://project‑intro")
def get_project_intro() -> str:
    """项目介绍文档，静态资源"""
    return """
本项目演示 MCP Resources能力
资源属于只读数据，适合配置、知识库、参考文档
"""


# 参数化动态资源：URI支持路径参数 {env}
@mcp.resource("config://{env}")
def get_env_config(env: str) -> str:
    """
    获取对应环境配置
    :param env: dev / test / prod
    """
    config_data = {
        "dev": '{"db_host":"127.0.0.1","debug":true}',
        "test": '{"db_host":"test‑db","debug":false}',
        "prod": '{"db_host":"online‑db","debug":false}'
    }
    return config_data.get(env, '{"error":"环境不存在"}')


if __name__ == "__main__":
    # stdio进程通信模式
    mcp.run(transport="stdio")
