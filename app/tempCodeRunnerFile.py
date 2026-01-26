from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# FastAPI 앱 초기화
app = FastAPI()

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
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    # 3. OpenAI LLM 초기화
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=1024
    )

    # 4. 프롬프트 템플릿 정의
    prompt_template = """
    You are an expert in infectious diseases. Provide accurate answers based strictly on the given context.

    Instructions:
    - Answer only using the provided context. Do not include creative ideas or answers not directly related to the question.
    - If the question is outside the context, respond with: "I don't know."
    - Provide the answer in Markdown format.
    - Include references in the "References" section using the source's URL from the metadata.
    - Answer in Korean.

    #Example Format (in Markdown):
        (detailed answer to the question)

        **출처**
        - (URL of the source)

    #Context:
    {context}

    #Question:
    {question}

    #Answer (in Markdown):
    """
    prompt = PromptTemplate(input_variables=["context", "question"], template=prompt_template)

    # 5. LLM 체인 생성
    llm_chain = prompt | llm

    # 6. RAG 체인 구성
    rag_chain = {"context": retriever, "question": RunnablePassthrough()} | llm_chain | StrOutputParser()

    print("RAG 체인이 성공적으로 초기화되었습니다!")

initialize_chain()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    메인 페이지 렌더링
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
async def query_endpoint(query_input: QueryInput):
    """
    사용자의 질문을 받아 RAG 체인을 통해 답변 생성
    """
    try:
        if rag_chain is None:
            raise RuntimeError("RAG 체인이 초기화되지 않았습니다.")
        result = rag_chain.invoke(query_input.query)
        return {"answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)