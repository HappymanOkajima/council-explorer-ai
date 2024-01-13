import requests
from bs4 import BeautifulSoup
import os
import re
import csv
from dotenv import load_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders.base import Document

def create_summarize_chain(llm):
    prompt_template = """あなたは有能な書記です。以下の議会議事録を要約してください。いずれも、固有名詞・年月・議案番号・金額については明記して省略しないように。議事の内容が報告の場合は、最初に、誰の何に対する報告かを簡潔に説明してください。内容が質問の場合は、最初に、誰のどの議案に対する質問なのかを説明してください。内容が答弁（質問に対する回答）の場合は、どの質問に対する答弁なのかを明記してください。内容が、議長による呼び出しのみの場合は、要約せずそのまま出力すれば構いません。挨拶など議事要旨と関係ない部分は不要です。

{text}

要約:"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = load_summarize_chain(llm, chain_type="map_reduce", return_intermediate_steps=False, map_prompt=PROMPT, combine_prompt=PROMPT)
    return chain

load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

pinecone.init(
    api_key=os.environ.get("PINECONE_API_KEY"),
    environment=os.environ.get("PINECONE_ENVIRONMENT")
)

with open('dump.csv', 'r', encoding="utf-8") as infile, open('summary.csv', 'a', encoding="utf-8") as outfile:
    csv_reader = csv.reader(infile,quotechar='"',quoting=csv.QUOTE_ALL,skipinitialspace=True)
    next(csv_reader)  # skip header

    header = '"meeting_name","statement_number","speaker_role","speaker_name","agenda_numbers","summary","source"\n'
    print(header)
    outfile.write(header)
    outfile.flush()

    for row in csv_reader:
        meeting_name, statement_number, speaker_role,speaker_name, agenda_numbers, content, source = row
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=6400, chunk_overlap=50)
        docs = text_splitter.create_documents(texts=[content])
       
        chain = create_summarize_chain(ChatOpenAI(model="gpt-4", streaming=True, verbose=True, temperature=0))
        summary = chain.run(docs)
        
        summary_doc = Document(page_content=summary, metadata={
            "source": source, 
            "meeting_name": meeting_name, 
            "speaker_role": speaker_role,
            "speaker_name": speaker_role,
            "agenda_numbers": agenda_numbers,
            "statement_number": statement_number
        })
        output_line = f"\"{meeting_name}\", \"{statement_number}\", \"{speaker_role}\", \"{speaker_name}\", \"{agenda_numbers}\", \"{summary}\", \"{source}\"\n"
        print(output_line)
        outfile.write(output_line)
        outfile.flush()
        
print("議事録要約がsummary.csvに保存されました。")

