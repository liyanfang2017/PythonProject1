from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
'''
llm = ChatOpenAI(
    base_url='https://open.bigmodel.cn/api/paas/v4',
    api_key='2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D',
    model='GLM-5.3',
    temperature=0.7
)
'''
# ---------------------- 1. 定义自定义工具函数 ----------------------
@tool
def get_current_time() -> str:
    """
    获取当前系统时间，当用户询问现在几点、当前日期、时间的时候调用此工具
    """
    now = datetime.now().strftime("%Y‑%m‑%d %H:%M:%S")
    return f"当前时间：{now}"


# 工具列表，可以放多个工具
tools = [get_current_time]

# ---------------------- 2. 初始化大模型 ----------------------
llm = ChatOpenAI(
    api_key="2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    model="GLM-5.3",
    temperature=0
)

# ---------------------- 3. Agent提示词模板 ----------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手，可以按需调用工具来回答用户问题。"),
    ("user", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# ---------------------- 4. 创建Agent & 执行器 ----------------------
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ---------------------- 5. 测试运行 ----------------------
if __name__ == "__main__":
    # 问题1：需要调用工具（问时间）
    res1 = agent_executor.invoke({"input": "现在几点了？"})
    print("sssssss")
    res2="123"
    print(res2)


    print("enddddd")
