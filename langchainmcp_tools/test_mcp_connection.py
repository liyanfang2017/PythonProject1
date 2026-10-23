"""
本地连通性测试：不调用真实 LLM，只验证 MCP Server 能正常启动、
工具能被发现和调用。
适配 langchain-mcp-adapters >= 0.3.0
"""
import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    # 用当前解释器启动 MCP Server 子进程，确保 mcp 包可用
    # 实际使用时可写 "python"，只要运行环境装了 mcp 即可
    python_path = sys.executable
    client = MultiServerMCPClient({
        "math": {
            "command": python_path,
            "args": ["math_server.py"],
            "transport": "stdio",
        }
    })

    # 新版用法：直接调用 get_tools（内部自动建立连接）
    tools = await client.get_tools()

    print("=" * 50)
    print("【1】MCP Server 暴露的工具列表:")
    for t in tools:
        print(f"  - {t.name}: {t.description[:60]}...")

    # 2. 找到 calculate 工具并直接调用
    calc_tool = next(t for t in tools if "calculate" in t.name)
    print("\n" + "=" * 50)
    print(f"【2】直接调用 {calc_tool.name}(\"12*34+56\"):")
    result = await calc_tool.ainvoke({"expression": "12*34+56"})
    print(f"  结果: {result}")

    # 3. 调用 add 工具
    add_tool = next(t for t in tools if "add" in t.name)
    print("\n" + "=" * 50)
    print(f"【3】直接调用 {add_tool.name}(a=100, b=200):")
    result = await add_tool.ainvoke({"a": 100, "b": 200})
    print(f"  结果: {result}")

    # 4. 调用 multiply 工具
    mul_tool = next(t for t in tools if "multiply" in t.name)
    print("\n" + "=" * 50)
    print(f"【4】直接调用 {mul_tool.name}(a=7, b=8):")
    result = await mul_tool.ainvoke({"a": 7, "b": 8})
    print(f"  结果: {result}")

    print("\n" + "=" * 50)
    print("✅ 所有测试通过！MCP Server 运行正常。")


if __name__ == "__main__":
    asyncio.run(main())
