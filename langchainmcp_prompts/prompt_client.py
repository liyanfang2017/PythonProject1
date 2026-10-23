"""
LangChain MCP Client：拉取远端Prompt模板 + 交给大模型执行
"""
import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    # 1. 连接本地MCP Prompt Server
    client = MultiServerMCPClient({
        "prompt_server": {
            "command": sys.executable,
            "args": ["prompt_server.py"],
            "transport": "stdio"
        }
    })

    # 2. 获取服务端发布的所有Prompt列表

    # async with client.session("prompt_server") as session:
    #     prompt_response = await session.list_prompts()
    #     prompt_list = prompt_response.prompts
    #prompt_list = await client.list_prompts("prompt_server")
    async with client.session("prompt_server") as session:
        prompt_response = await session.list_prompts()
        prompt_list = prompt_response.prompts
        print("===== MCP Server 可用的Prompt模板 =====")
        for p in prompt_list:
            print(f"- name:{p.name}, desc:{p.description}")

    # ------------------------------
    # 案例A：调用 summarize_content 模板
    # ------------------------------
    print("\n===== 案例A：调用摘要Prompt模板 =====")
    messages_a = await client.get_prompt(
        server_name="prompt_server",
        prompt_name="summarize_content",
        arguments={
            "text": "MCP协议是模型上下文协议，可以实现LLM与外部工具、资源、提示模板的解耦，支持跨进程通信。",
            "style": "简洁"
        }
    )
    print("从MCP获取到的消息列表：")
    for msg in messages_a:
        print(f"[{msg.type}] {msg.content}")

    # 初始化LLM（智谱glm‑4‑flash，兼容OpenAI接口，替换成你自己的api‑key）
    llm = ChatOpenAI(
        base_url=os.getenv("ZHIPU_BASE_URL"), api_key=os.getenv("ZHIPU_API_KEY"), model=os.getenv("ZHIPU_MODEL"),
        temperature=0
    )

    # 将远端拉取到的Prompt消息直接丢给LLM执行
    resp_a = await llm.ainvoke(messages_a)
    print("\nLLM执行Prompt返回结果：")
    print(resp_a.content)

    # ------------------------------
    # 案例B：调用多轮代码审查Prompt模板
    # ------------------------------
    print("\n===== 案例B：调用代码审查多轮Prompt模板 =====")
    messages_b = await client.get_prompt(
        server_name="prompt_server",
        prompt_name="code_review_prompt",
        arguments={
            "language": "python",
            "target": "安全"
        }
    )
    # 追加用户侧的代码内容
    from langchain_core.messages import HumanMessage
    code_snippet = """
def calc(a,b):
    return eval(f"{a}+{b}")
"""
    messages_b.append(HumanMessage(content=code_snippet))

    for msg in messages_b:
        print(f"[{msg.type}] {msg.content}")

    resp_b = await llm.ainvoke(messages_b)
    print("\nLLM代码审查结果：")
    print(resp_b.content)

    # 关闭子进程连接
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
