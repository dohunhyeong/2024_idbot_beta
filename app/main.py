import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import pymongo

# -- 데이터베이스 접속
conn = pymongo.MongoClient(f'mongodb://openai:pw_509@211.54.28.173:37017/openai')

# -- db선택
db = conn.get_database("openai")

# -- 컬렉션 선택
collection = db.get_collection('QA_data')

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 템플릿 설정
templates = Jinja2Templates(directory="app/templates")

# 환경 변수 로드
load_dotenv()

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class QueryInput(BaseModel):
    query: str

# 전역 변수로 RAG 체인 선언
rag_chain = None

def initialize_chain():
    """
    RAG 체인 초기화 함수
    """
    global rag_chain

    # 파일 경로
    folder_path = "./data"

    # 1. OpenAI 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    # 2. FAISS 데이터베이스 로드
    db = FAISS.load_local(
        folder_path=folder_path,
        embeddings=embeddings,
        index_name='faiss_index',
        allow_dangerous_deserialization=True
    )

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 2, "fetch_k" : 5})
    
    # 3. OpenAI LLM 초기화
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_tokens=1500
    )

    # 4. 프롬프트 템플릿 정의
    prompt_template = """
    당신은 감염병 전문가입니다. 반드시 정확한 답을 해주시며, 동일한 질문에는 같은 대답을 해주세요.

    Instructions:
    - 당신에 대해서 물어볼 때만 '법정감염병 알아보기 챗봇입니다.'라고 대답해주세요. 해당 사항 외에는 '법정감염병 알아보기 챗봇입니다.'라는 대답을 할 필요 없습니다.
    - 인사를 할 땐 인사로 답해주세요.
    - 반드시 "retriver"에 검색된 문서만을 활용하여 대답해주세요.
    - 만일 적절한 대답을 발견하지 못했을 때, '잘 모르겠습니다.'로 대답해주세요. 
    - 아래의 제공된 #Example Format을 참고하여 Markdown 형식으로 대답해주세요.
    - Include references in the "출처" section using the source's URL from the metadata.
    - 모든 대답은 한국어로 해주세요.

    #Example Format (in Markdown):
        (질문에 대한 자세한 답변)

        **출처**
        - (URL)

    #Context:
    {context}

    #Question:
    {question}

    #Answer (in Markdown):
    """
    prompt = PromptTemplate(input_variables=["context", "question"], template=prompt_template)

    # 5. 컨텍스트 문서 + 출처 문자열 생성 함수
    def fetch_context_and_sources(question: str) -> str:
        docs = retriever.invoke(question)
        context_blocks = []
        for doc in docs:
            text = doc.page_content.strip()
            source = doc.metadata.get("source", "출처 없음").strip()
            context_blocks.append(f"{text}\n출처: {source}")
        return "\n\n".join(context_blocks)

    # 6. RAG 체인 생성
    rag_chain = (
        {
            "context": fetch_context_and_sources,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    print("✅ RAG 체인이 성공적으로 초기화되었습니다!")


initialize_chain()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    메인 페이지 렌더링
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/test/{msg}")
async def get_message(msg: str):
    return {"received_message": msg}

@app.post("/query")
async def query_endpoint(request: Request, query_input: QueryInput):
    """
    사용자의 질문을 받아 RAG 체인을 통해 답변 생성
    """
    try:
        if rag_chain is None:
            raise RuntimeError("RAG 체인이 초기화되지 않았습니다.")
        
        input_date = datetime.now()
        query_string = query_input.query
        client_ip = request.client.host
        
        result = rag_chain.invoke(query_input.query)
        output_date = datetime.now()
        
        # MongoDB에 로그 저장
        log_data = {
            "clientIp": client_ip,
            "inputDate": input_date,
            "queryString": query_string,
            "outputDate": output_date,
            "result": result
        }
        
        # MongoDB 컬렉션에 로그 데이터 삽입
        collection.insert_one(log_data)
        
        return {"answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)