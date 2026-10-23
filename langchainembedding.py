#langchain支持嵌入模型的示例 待分析，嵌入模型的使用场景 及 示例
#向量存储的示例
import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
# 1.初始化嵌入模型
# embedding = HuggingFaceEmbeddings(
#     model_name="BAAI/bge-small-zh-v1.5",
#     model_kwargs={"device":"cpu"},
#     encode_kwargs={"normalize_embeddings":True}
# )

embedding = OpenAIEmbeddings(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url=os.getenv("ZHIPU_BASE_URL"),
    model="embedding-3"
)


# 2.准备知识库文本
texts = [
    "LangChain是一个用来构建大模型应用的开源框架，支持链、Agent、RAG知识库",
    "嵌入模型可以将文本转为向量，实现语义搜索",
    "RAG检索增强生成，先检索知识库再交给大模型回答问题，可以降低幻觉问题",
    "向量数据库专门用来存储文本嵌入向量，支持相似度搜索",
    "Milvus是一款开源高性能生产级向量数据库，适合大规模知识库"
]

# 3.创建向量库，持久化保存到磁盘 ./chroma_db
persist_dir = "./chroma_db"
db = Chroma.from_texts(
    texts=texts,
    embedding=embedding,
    persist_directory=persist_dir
)

# ----------------- 4.语义相似度检索 ----------------------
query = "什么是RAG？"

# k=2 返回相似度最高2条结果
docs = db.similarity_search(query, k=2)

print("===语义检索结果===")
for idx, doc in enumerate(docs):
    print(f"{idx+1}. {doc.page_content}")

# 带分数检索，返回相似度距离值
docs_with_score = db.similarity_search_with_score(query, k=2)
for doc, score in docs_with_score:
    print(f"相似度分数:{score}, 内容:{doc.page_content}")


# -----------------5.重新加载已经持久化的向量库(程序重启不用重新向量化)----------------
db2 = Chroma(
    persist_directory=persist_dir,
    embedding_function=embedding
)

# 6.转为检索器Retriever，RAG链标准接口
retriever = db2.as_retriever(search_kwargs={"k":2})
res = retriever.invoke("LangChain能干什么")
print(res[0].page_content)

