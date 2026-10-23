'''
deepseek 模型
sk-7fa969ac85de40f780cb59eb16186623
https://api.deepseek.com
deepseek-v4-flash
智普
2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D
https://open.bigmodel.cn/api/paas/v4
GLM-5.3
'''

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

#1初始化大模型
llm = ChatOpenAI(
    base_url='https://open.bigmodel.cn/api/paas/v4',
    api_key='2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D',
    model='GLM-5.3',
    temperature=0.7
)

#2构造提示词模版
prompt = ChatPromptTemplate.from_messages(
    [
    ("system", "你是一名资深Java工程师，回答简洁精炼"),
    ("human", "{question}")
])


#3 输出解析
parser = StrOutputParser()
#4 构造链
chain = prompt | llm | parser

#5 执行调用
res = chain.invoke({"question":"回答下langchain的核心作用及工作原理"})
print(res)



