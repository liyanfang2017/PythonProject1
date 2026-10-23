from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(
    base_url='https://open.bigmodel.cn/api/paas/v4',
    api_key='2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D',
    model='GLM-5.3',
    temperature=0.7
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是聊天助手，记住上下文对话内容"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

parser = StrOutputParser()

chain = prompt | llm | parser
#存储历史会话
store = {}


def  get_session_history(sessionid:str):
    if sessionid not in store:
        store[sessionid] = InMemoryChatMessageHistory()
    return store[sessionid]

with_history_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)


#第一轮对话

req1= with_history_chain.invoke({"input":"我的名字叫张三"},
    config={"configurable":{"session_id":"sid_001"}})
print(req1)

req2 = with_history_chain.invoke({"input":"我的名字叫李四"},
    config={"configurable":{"session_id":"sid_002"}})

print(req2)

req3 = with_history_chain.invoke(
{"input":"我叫什么名字?"},
    config={"configurable":{"session_id":"sid_001"}}
)

print(req3)
