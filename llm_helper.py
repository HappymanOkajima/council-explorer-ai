import os
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
import pinecone
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from llm_retriver import LLMRetriever

load_dotenv()
openai_model = os.environ.get("OPENAI_MODEL","gpt-4")

def _initialize_environment():
    pinecone.init(
        api_key=os.environ.get("PINECONE_API_KEY"),
        environment=os.environ.get("PINECONE_ENVIRONMENT")
    )
    index_name = os.environ.get("PINECONE_INDEX")
    return index_name

def _create_objects(index_name, callback):
    embeddings = OpenAIEmbeddings()
    db = Pinecone.from_existing_index(index_name, embeddings)

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
    chain = LLMChain(llm=llm, prompt=PROMPT, verbose=True)
    return db, chain

def _initialize(callback):
    index_name = _initialize_environment()
    db, chain = _create_objects(index_name, callback)
    return db, chain

def _retrieve_documents(db, question, filter=None, k=None):
    """
    質問に関連するドキュメントをデータベースから取得する関数。

    引数:
    db -- データベース
    question -- ユーザーからの質問
    filter -- ドキュメントのフィルタリング条件（オプション）
    k -- 取得するドキュメントの数（オプション）
    """

    # フィルタとkが指定されている場合
    if filter and k:
        # データベースの類似性検索機能を使用して、フィルタに一致する上位kのドキュメントを取得
        docs = db.similarity_search(question, k=k, filter=filter)
    else:
        # フィルタやkが指定されていない場合、LLMRetrieverを使用して関連するドキュメントを取得
        retriever = LLMRetriever(db=db, llm=ChatOpenAI(model=openai_model, temperature=0))
        docs = retriever.get_relevant_documents(question)
    # 取得したドキュメントを返す
    return docs

def answer_by_self_query(question, callback):
    db, chain = _initialize(callback)
    docs = _retrieve_documents(db, question)
    context = "\n".join([doc.page_content for doc in docs])
    chain.predict(context=context, topic=question)
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
    db, chain = _initialize(callback)
    # フィルタリング条件と一致するドキュメントを取得
    docs = _retrieve_documents(db, question, filter=filter, k=k)
    # 取得したドキュメントの内容を連結
    context = "\n".join([doc.page_content for doc in docs])
    # 連結したドキュメントの内容と質問を元に予測を行う
    chain.predict(context=context, topic=question)
    # 取得したドキュメントを返す
    return docs