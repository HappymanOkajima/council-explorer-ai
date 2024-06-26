import os
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from pinecone import Pinecone 
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from llm_retriver import LLMRetriever
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
openai_model = os.environ.get("OPENAI_MODEL","gpt-4")

def _create_chain(callback):
    prompt_template = """コンテキストにある情報のみを用いて、トピックに対応する日本語の回答をしてください。
    Context: {context}
    Topic: {topic}
    回答:"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "topic"]
    )

    llm = ChatOpenAI(
        model=openai_model,
        streaming=True,
        callbacks=[callback],
        verbose=True,
        # max_tokens=1500,
        temperature=0.0,
    )
    chain = PROMPT | llm
    
    return chain

def _initialize_vectorstore():
    Pinecone(
        api_key=os.environ.get("PINECONE_API_KEY"),
    )
    index_name = os.environ.get("PINECONE_INDEX")
    embeddings = OpenAIEmbeddings()
    db = PineconeVectorStore.from_existing_index(index_name, embeddings)
    
    return db

def answer_by_self_query(question, callback):
    """
    ドキュメントから質問に答える関数。

    引数:
    question -- ユーザーからの質問
    callback -- コールバック関数
    """
    # データベースとチェーンを初期化
    db = _initialize_vectorstore()
    chain = _create_chain(callback)
    
    retriever = LLMRetriever(db=db, llm=ChatOpenAI(model=openai_model, temperature=0))
    docs = retriever.get_relevant_documents(question)
    context = "\n".join([doc.page_content for doc in docs])
    chain.invoke({"context": context, "topic": question})
    return docs

def answer_by_filter(question, filter, k, callback):
    """
    フィルタリング条件と一致するドキュメントから質問に答える関数。

    引数:
    question -- ユーザーからの質問
    filter -- ドキュメントのフィルタリング条件
    k -- 取得するドキュメントの数
    callback -- コールバック関数
    """

    # データベースとチェーンを初期化
    db = _initialize_vectorstore()
    chain = _create_chain(callback)

    # データベースの類似性検索機能を使用して、フィルタに一致する上位kのドキュメントを取得
    docs = db.similarity_search(question, k=k, filter=filter)
    # 取得したドキュメントの内容を連結
    context = "\n".join([doc.page_content for doc in docs])
    # 連結したドキュメントの内容と質問を元に予測を行う
    chain.invoke({"context": context, "topic": question})
    
    # 取得したドキュメントを返す
    return docs

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
class StreamHandler(StreamingStdOutCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(token, end='', flush=True)

if __name__ == "__main__":
    res = answer_by_self_query("高浜町の議会の概要",StreamHandler())
