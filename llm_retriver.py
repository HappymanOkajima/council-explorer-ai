# llm_retriever.py

from langchain.llms import OpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
import pinecone
import os
from dotenv import load_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

class LLMRetriever:
    def __init__(self, db=None, llm=None):
        self.db = db
        self.llm = llm

        if self.db is None or self.llm is None:
            load_dotenv()
            self.api_key = os.environ.get("PINECONE_API_KEY")
            self.environment = os.environ.get("PINECONE_ENVIRONMENT")
            self.index_name = os.environ.get("PINECONE_INDEX")
            self._initialize_resources()

        self._init_retriever()

    def _initialize_resources(self):
        pinecone.init(
            api_key=self.api_key,
            environment=self.environment
        )

        embeddings = OpenAIEmbeddings()
        self.db = Pinecone.from_existing_index(self.index_name, embeddings)
        
        self.llm = OpenAI(temperature=0)

    def _init_retriever(self):
        metadata_field_info=[
            AttributeInfo(
                name="agenda_numbers",
                description="議案番号。議案第N号と表記されることもある", 
                type="string or list[string]", 
            ),
            AttributeInfo(
                name="meeting_name",
                description="会議名",
                type="string", 
            ),
            AttributeInfo(
                name="speaker_role",
                description="発言者の役割や肩書。議長・町長・議会事務局長・総務課長・教育長・住民生活課長・保健福祉課長・上下水道課長・教育委員会事務局長・防災安全課長", 
                type="string", 
            ),
            AttributeInfo(
                name="speaker_name",
                description="発言者の名前。通常「君」で終わる", 
                type="string", 
            ),
            AttributeInfo(
                name="statement_number",
                description="発言番号", 
                type="integer", 
            ),
            AttributeInfo(
                name="source",
                description="この議事録概要のソースとなるURL", 
                type="string", 
            ),
            # AttributeInfo(
            #     name="text",
            #     description="議事概要", 
            #     type="string", 
            # ),
          
        ]

        document_content_description = "高浜町議会の議事概要"
        
        self.retriever = SelfQueryRetriever.from_llm(
            self.llm, 
            self.db, 
            document_content_description, 
            metadata_field_info, 
            verbose=True,
            enable_limit=True
        )

    def get_relevant_documents(self, query):
        pre_query = "議長の発言でない、"
        post_query = "（件数は20件）"
        return self.retriever.get_relevant_documents(pre_query + query + post_query)
      
if __name__ == "__main__":
    retriever = LLMRetriever()
    
    res = retriever.get_relevant_documents("町長の発言")
    # res = retriever.get_relevant_documents("議長の発言でない、議案番号3が含まれる話題を要約して")
    print("-------")
    print(res)
    print(len(res))

