from typing import Any
from uuid import UUID
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import ChatMessage
from langchain.schema.output import LLMResult
import streamlit as st
import tiktoken
import os
from langchain.callbacks.base import BaseCallbackHandler
from llm_helper import answer_by_filter
from dataclasses import dataclass

load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

@dataclass
class Result:
    value: str

@st.cache_resource
def create_prompt():

    prompt_template = """あなたはアシスタントAIで質問者であるHumanをサポートします。
質問には、以下のテキストに含まれる情報を踏まえて回答してください。

Context:
```
{topic}    
```
  
{chat_history}

Human:{question}
AI:"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["question","chat_history","topic"]
    )
    
    return PROMPT
  
def extract_content_pairs(messages):
    return [f"Human: \"{messages[i].content}\",AI: \"{messages[i+1].content}\"" for i in range(0, len(messages), 2)]

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)
        
class RetriverStreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)
        
    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        result_text.value = self.text
        return super().on_llm_end(response, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

def bulid_source_link(docs):
    text = ""
    if not docs:
        text += "\n\n関連する議事録が見つかりませんでした。"
    else:
        text += "\n\n現在話題にしている議事録は{}件です。\n\n".format(len(docs))
        for doc in docs:
            link_text = f"{doc.metadata['meeting_name']} 発言番号{doc.metadata['statement_number']} {doc.metadata['speaker_name']}'"
            link_url = doc.metadata["source"]
            text += " 1. [{}]( {} )\n".format(link_text, link_url)
    return text


def count_tokens(question,history,topic):
    tokenizer = tiktoken.encoding_for_model("gpt-4")
    question_tokens = len(tokenizer.encode(question))
    history_tokens = [len(tokenizer.encode(h)) for h in history]
    topic_tokens = len(tokenizer.encode(topic))
    buffer = 100
    return question_tokens + sum(history_tokens) + topic_tokens + buffer

def reset_chat():
    st.session_state["topic"] = ChatMessage(role="assistant", content="")
    st.session_state["messages"].clear()
    st.session_state["source_link"] = ""
   
def create_filter(meeting_name,speaker_name,agenda_numbers,exclude_chairman):
    filter = {}
    if (exclude_chairman):
        filter["speaker_role"] = {"$ne": "議長"}
    if meeting_name:
        filter["meeting_name"] = {"$eq": meeting_name}
    if speaker_name:
        filter["speaker_name"] = {"$eq": speaker_name}
    if agenda_numbers:
        filter["agenda_numbers"] = {"$eq": agenda_numbers}

    return filter

# サイドバー
with st.sidebar:
    st.title('議事録分析ChatBot')
    # st.subheader('最初に話題を決めてください')

    col1, col2 = st.columns(2)
    with col1:
        with open('meetings.txt', 'r', encoding='utf-8') as f:
            meetings = [line.strip() for line in f]

        meeting_name = st.selectbox('いつの（会議）', ('', *meetings))
        
        with open('speakers.txt', 'r', encoding='utf-8') as f:
            speakers = [line.strip() for line in f]

        speaker_name = st.selectbox('誰の（発言者）', ('', *speakers))

    with col2:
        agenda_numbers = st.text_input('何に関する（議案・一般質問）',placeholder="1",help="議案番号の番号、または一般質問の順番を数字で入力してください")
        general_question = st.checkbox('一般質問',help="一般質問の場合はチェックしてください")
        if general_question & (agenda_numbers != ""):
            agenda_numbers = "一般質問その" + agenda_numbers

    # question = st.text_area('キーワードなど')
    question = "300文字で要約して。"
    col1, col2 = st.columns(2)
    with col1:
        include_source = st.checkbox('議事録リンクを表示する',value=True,help="現在話題にしている議事録のリンクを画面左側に表示できます")
    with col2:
        exclude_chairman = st.checkbox('議長発言を対象外とする',help="探索対象から議長の発言を外すことで、より多くの関連議事録を探索できます。")
    k = st.slider('探索する議事録の上限数', 1, 75, 200,help="関連度の高い上位何件までを探索対象とするか指定します。大きすぎると関係のない議事も選ばれることがあります。")
    
    action = st.button('話題にする')
        
    result_text = Result(value="")
    retriver_area = st.empty()

    if (action):
        retriver_handler = RetriverStreamHandler(retriver_area)
        filter = create_filter(meeting_name,speaker_name,agenda_numbers,exclude_chairman)
        print(filter,k)
        docs = answer_by_filter(question,filter,k,retriver_handler)
        # statement_number でソート
        sorted_docs = sorted(docs, key=lambda doc: (doc.metadata['meeting_name'], int(doc.metadata['statement_number'])))
        # ソートされた docs を使って context を作成
        context = "\n".join([f"{doc.page_content}（発言番号：{doc.metadata['statement_number']}）" for doc in sorted_docs])
        st.session_state.messages.append(ChatMessage(role="user", content=question))
        st.session_state.messages.append(ChatMessage(role="assistant", content=result_text.value))
        st.session_state["topic"] = ChatMessage(role="assistant", content=context) 
        print(st.session_state["topic"].content)
        if (include_source):
            st.session_state.source_link = bulid_source_link(sorted_docs)

    if "source_link" not in st.session_state:
        st.session_state["source_link"] = ""
     
    retriver_area.markdown(st.session_state.source_link)
    
# メインパネル
if "topic" not in st.session_state:
    st.session_state["topic"] = ChatMessage(role="assistant", content="")
    
if "messages" not in st.session_state:
    st.session_state["messages"] = []
 
for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if chat_prompt := st.chat_input("話題についての質問や相談をどうぞ"):
    openai_model = os.environ.get("OPENAI_MODEL","gpt-4")
    st.chat_message("user").write(chat_prompt)
    history = extract_content_pairs(st.session_state.messages)
    token_size = count_tokens(chat_prompt,history,st.session_state["topic"].content)

    # openai_modelの値に基づいてtoken_maxを設定
    if openai_model == 'gpt-3.5-turbo-16k':
        token_max = 15500
    elif openai_model == 'gpt-4':
        token_max = 7500
    elif openai_model == 'gpt-4-1106-preview':
        token_max = 128000
    else:
        token_max = 3500
       
    warn_message = f"DEBUG: model = {openai_model},token_size = {token_size}"
        
    if (token_size > token_max):
        st.session_state.messages.pop(0)
        st.session_state.messages.pop(0) 
        warn_message = "**（記憶容量が許容値を超えそうだったので、一番古い会話履歴を消しました。そろそろ話題をリセットしても良いかもしれません）**"

    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())
        prompt = create_prompt()
        llm = ChatOpenAI(model=openai_model, openai_api_key=openai_api_key, streaming=True, callbacks=[stream_handler])
        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
        response = chain.run(question = chat_prompt, chat_history = history, topic = st.session_state["topic"].content)
        st.session_state.messages.append(ChatMessage(role="user", content=chat_prompt))
        st.session_state.messages.append(ChatMessage(role="assistant", content=response))
        if (warn_message):
            st.write(warn_message)
        
reset = st.button(f'話題をリセットする',on_click=reset_chat)    



