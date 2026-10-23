#langchain支持多智能体构建示例
#Supervisor 主管路由多智能体（LangGraph 实现，生产推荐）
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
import operator

load_dotenv()
llm = ChatOpenAI(base_url=os.getenv("ZHIPU_BASE_URL"),api_key=os.getenv("ZHIPU_API_KEY"), model=os.getenv("ZHIPU_MODEL"),temperature=0)
# llm = ChatOpenAI(
#     base_url='https://open.bigmodel.cn/api/paas/v4',
#     api_key='2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D',
#     model='glm-4',
#     temperature=0.7
# )
# ========== 1. 定义全局状态，保存所有Agent对话历史 ==========
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], operator.add]
    next: str

# ========== 2. 创建各个专家Agent节点 ==========
# 代码专家
def agent_coder(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是资深编程工程师，专门解答代码、开发、技术问题，回答简洁专业。"),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | llm
    res = chain.invoke(state["messages"])
    return {"messages":[res]}

# 文案专家
def agent_writer(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业文案写手，擅长写文案、演讲稿、小故事。"),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | llm
    res = chain.invoke(state["messages"])
    return {"messages":[res]}

# 数学专家
def agent_math(state: AgentState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是数学老师，精确解答数学计算题，写出计算步骤。"),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | llm
    res = chain.invoke(state["messages"])
    return {"messages":[res]}

# ========== 3.主管路由Agent：判断交给谁处理 ==========
supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """你是任务主管。根据用户问题，选择交给哪个专家处理：
可选专家：
coder: 编程、代码、技术开发问题
writer: 文案、写作、演讲稿、故事
math: 数学计算、算术题
只返回专家名字，只能返回这三个单词其中一个：coder / writer / math
"""),
    MessagesPlaceholder(variable_name="messages"),
])
# 路由输出结构化
from langchain_core.output_parsers import StrOutputParser
supervisor_chain = supervisor_prompt | llm | StrOutputParser()

def supervisor(state: AgentState):
    decision = supervisor_chain.invoke(state)
    return {"next": decision.strip()}

# ==========4.构建流程图 ==========
builder = StateGraph(AgentState)
# 添加节点
builder.add_node("supervisor", supervisor)
builder.add_node("coder", agent_coder)
builder.add_node("writer", agent_writer)
builder.add_node("math", agent_math)

# 入口先进入主管
builder.add_edge(START, "supervisor")


# 条件路由：主管结果跳转到对应专家
builder.add_conditional_edges(
    "supervisor",
    lambda x: x["next"],
    {
        "coder": "coder",
        "writer": "writer",
        "math": "math"
    }
)
# 专家回答完直接结束
builder.add_edge("coder", END)
builder.add_edge("writer", END)
builder.add_edge("math", END)

graph = builder.compile()

# ==========运行测试 ==========
if __name__ == "__main__":
    # 测试1：代码问题，路由给coder
    result = graph.invoke({
        "messages":[HumanMessage(content="用python写一个快速排序")]
    })
    print("回答：", result["messages"][-1].content)

    # 测试2：文案问题，路由给writer
    # result = graph.invoke({"messages":[HumanMessage(content="写一段春天风景的短文")]})
    # print("回答：", result["messages"][-1].content)