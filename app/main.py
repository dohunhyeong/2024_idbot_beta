import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from fastapi.middleware.cors import CORSMiddleware
from langfuse.langchain import CallbackHandler
from langfuse import observe, get_client

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

# Langfuse trace 이름 (환경변수로 설정, 기본값 "s1")
SYSTEM_NAME = os.getenv("SYSTEM_NAME", "s1")

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

    # 파일 경로 (환경변수로 오버라이드 가능)
    folder_path = os.getenv("FAISS_FOLDER_PATH", "./data")

    # 1. 임베딩 모델 초기화 (bge-m3, 1024차원)
    embeddings = OllamaEmbeddings(model="bge-m3")

    # 2. FAISS 데이터베이스 로드
    db = FAISS.load_local(
        folder_path=folder_path,
        embeddings=embeddings,
        index_name=os.getenv("FAISS_INDEX_NAME", "faiss_index"),
        allow_dangerous_deserialization=True
    )

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    
    # 3. OpenAI LLM 초기화
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )

    # 4. 프롬프트 템플릿 정의
    prompt_template ="""
        당신은 감염병 일반 전문가입니다.

        반드시 제공된 Context 문서만 사용하여 답변하세요.
        문서에 없는 내용은 추측하지 마세요.
        
        #Example Format (in Markdown):
        (질문에 대한 자세한 답변)

        **출처**
        - (URL)
        
        Context:
        {context}

        Question:
        {question}

        Answer (한국어):
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
@observe()
async def query_endpoint(query_input: QueryInput):
    """
    사용자의 질문을 받아 RAG 체인을 통해 답변 생성
    """
    try:
        if rag_chain is None:
            raise RuntimeError("RAG 체인이 초기화되지 않았습니다.")

        get_client().update_current_span(name=SYSTEM_NAME)

        langfuse_handler = CallbackHandler()
        result = rag_chain.invoke(
            query_input.query,
            config={"callbacks": [langfuse_handler]}
        )

        return {"answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)