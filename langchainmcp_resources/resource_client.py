"""
LangChain MCP Client 读取服务端 Resources 资源
完整可运行代码
"""
import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    # 1.连接资源服务端
    client = MultiServerMCPClient({
        "resource_server": {
            "command": sys.executable,
            "args": ["resource_server.py"],
            "transport": "stdio"
        }
    })

    # ==========1.列出Server上所有可用资源（底层session原生调用）==========
    async with client.session("resource_server") as session:
        res_list_resp = await session.list_resources()
        resource_list = res_list_resp.resources
        print("===== MCP Server 全部可用资源列表 =====")
        for item in resource_list:
            print(f"uri: {item.uri}, name:{item.name}, desc:{item.description}")

    # ==========2.读取单个静态资源 info://project‑intro ==========
    print("\n=====读取静态资源 project‑intro =====")
    blobs_static = await client.get_resources(
        server_name="resource_server",
        uris=["info://project‑intro"]
    )
    for blob in blobs_static:
        print(f"URI: {blob.metadata['uri']}")
        print("资源文本内容：")
        print(blob.as_string())

    # ==========3.读取动态参数资源 config://dev / config://prod ==========
    print("\n=====读取动态资源‑开发环境配置 config://dev =====")
    blobs_dev = await client.get_resources(
        server_name="resource_server",
        uris=["config://dev"]
    )
    for blob in blobs_dev:
        print(blob.as_string())

    print("\n=====读取动态资源‑生产环境配置 config://prod =====")
    blobs_prod = await client.get_resources(
        server_name="resource_server",
        uris=["config://prod"]
    )
    for blob in blobs_prod:
        print(blob.as_string())

    # ==========4.把读取到的资源内容交给LLM使用（拓展示例）==========
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(api_key="xxx", base_url="xxx", model="glm‑4‑flash")
    # content = blobs_static[0].as_string()
    # resp = await llm.ainvoke(f"解读下面这份文档：{content}")
    # print(resp.content)

    #await client.close()


if __name__ == "__main__":
    asyncio.run(main())
