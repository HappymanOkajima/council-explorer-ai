import os
import ast
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
import pinecone
from langchain_core.documents import Document


load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

# initialize pinecone
pinecone.init(
    api_key=os.environ.get("PINECONE_API_KEY"),
    environment=os.environ.get("PINECONE_ENVIRONMENT")
)

index_name = os.environ.get("PINECONE_INDEX")
embeddings = OpenAIEmbeddings()

import csv

def process_row(row):
    # この関数内で各行に対する処理を行う
    meeting_name = row['meeting_name']
    statement_number = row['statement_number']
    speaker_role = row['speaker_role']
    speaker_name = row['speaker_name']
   
    agenda_numbers = row['agenda_numbers']
    summary = row['summary']
    source = row['source']
    
    
    docs = [Document(page_content=summary, metadata={
        "source": source,
        "meeting_name": meeting_name, 
        "speaker_role": speaker_role,
        "speaker_name": speaker_name,
        "agenda_numbers": ast.literal_eval("[" + agenda_numbers + "]"),
        "statement_number": statement_number,
        "text": summary
        })]
    Pinecone.from_documents(docs, embeddings, index_name=index_name)
    print(docs)
    

def main():
    with open('edited_summary.csv', 'r', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile,quotechar='"',quoting=csv.QUOTE_ALL,skipinitialspace=True)  # ヘッダを考慮して各行を辞書として読み込む
        for row in reader:
            process_row(row)

if __name__ == '__main__':
    main()
