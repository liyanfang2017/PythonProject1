# langchain支持mcp协议的示例  待分析，mcp的使用场景及示例
#mcp协议 与 openai协议的区别 及 优缺点分析 ，及什么场景使用openai，什么场景使用mcp
# langchain_mcp_client.py
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

async def main():
    # 连接一个或多个MCP服务
    client = MultiServerMCPClient({
        "math":{
            "command":"python",
            "args":["math_server.py"],
            "transport":"stdio"
        }
    })
    async with client:
        # 获取MCP导出的工具列表，自动转为LangChain标准BaseTool
        tools = await client.get_tools()

        # 可替换成智谱/通义千问等任意大模型
        llm = ChatOpenAI(
            api_key="xxx",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            model="glm-4-flash"
        )
        # 创建LangGraph ReAct Agent
        agent = create_react_agent(llm,tools)
        res = await agent.ainvoke({"messages":["计算 12*34+56"]})
        print(res["messages"][-1].content)

if __name__=="__main__":
    asyncio.run(main())