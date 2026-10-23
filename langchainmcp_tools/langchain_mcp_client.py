"""
LangChain MCP Client 示例
连接本地 math_server.py，通过 ReAct Agent 调用 MCP 工具完成计算。

适配 langchain-mcp-adapters >= 0.3.0
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    # ===== 1. 连接 MCP Server =====
    # 这里通过 stdio 启动本地 math_server.py 子进程
    # 也可以连接远程 Server（transport=sse/http）
    client = MultiServerMCPClient({
        "math": {
            "command": "python",
            "args": ["math_server.py"],
            "transport": "stdio",
        }
    })

    # ===== 2. 自动获取 MCP 暴露的工具列表 =====
    # Server 上的 calculate / add / multiply 会自动转为 LangChain BaseTool
    # 新版用法：直接调用 get_tools（内部自动建立连接）
    tools = await client.get_tools()
    print(f"已加载 MCP 工具: {[t.name for t in tools]}\n")

    # ===== 3. 初始化大模型 =====
    # 这里用智谱 AI 作为示例（兼容 OpenAI API 格式）
    # 也可以换成 DeepSeek / 通义千问 / 月之暗面等，只需改 base_url 和 model
    llm = ChatOpenAI(
        base_url=os.getenv("ZHIPU_BASE_URL"), api_key=os.getenv("ZHIPU_API_KEY"), model=os.getenv("ZHIPU_MODEL"),
        temperature=0,
    )

    # ===== 4. 创建 ReAct Agent =====
    # Agent 会自动判断是否需要调用工具，形成"思考-行动-观察"循环
    agent = create_react_agent(llm, tools)

    # ===== 5. 调用 Agent =====
    query = "计算 12*34+56，然后再加上 100"
    print(f"用户提问: {query}\n")

    res = await agent.ainvoke({"messages": [query]})

    # 打印最终回答
    print("=" * 50)
    print("Agent 最终回答:")
    print(res["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
