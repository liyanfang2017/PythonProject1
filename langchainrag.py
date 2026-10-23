from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

#llm = ChatOpenAI(api_key="2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D",model="GLM-5.3")

llm = ChatOpenAI(
    base_url='https://open.bigmodel.cn/api/paas/v4',
    api_key='2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D',
    model='glm-4',
    temperature=0.7
)
# ========= 重点修复！Embedding也必须加智谱base_url =========
embedding = OpenAIEmbeddings(
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key="2525b5ba0b4347d8a961caee84479b8f.BfkPHCybgRMiBZ4D",
    model="embedding-3"    # 智谱向量模型名称
)

# 1.原始文档文本
text = """
Dify是一款低代码AI应用开发平台。
用户无需编写LangChain代码，可视化拖拽即可搭建Agent智能体、知识库RAG应用。
底层技术栈：Python FastAPI后端、React前端，docker一键部署。
"""
# 2.文本切分
splitter = RecursiveCharacterTextSplitter(chunk_size=150,chunk_overlap=20)
chunks = splitter.split_text(text)

# 3.存入向量库
db = Chroma.from_texts(chunks,embedding)
retriever = db.as_retriever(search_kwargs={"k":2})

# 4.RAG提示词
rag_prompt = ChatPromptTemplate.from_template("""
基于下面知识库内容回答问题，不知道就如实说不知道：
{context}
问题:{question}
""")

# 构建RAG链
rag_chain = (
    {"context": retriever | (lambda docs:"\n".join([d.page_content for d in docs])),
     "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

# 查询
ans = rag_chain.invoke("Dify是什么？")
print(ans)
