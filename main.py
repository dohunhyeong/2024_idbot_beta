import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import bs4
import traceback

# 사용자가 입력한 내용을 변환(파싱)해주는 모듈
from pydantic import BaseModel

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# Load environment variables
load_dotenv()

app = FastAPI()

# 정적 파일 제공 설정
# mount 함수: 해당 경로에 있는 내용들을 마운트하겠다는 의미.
# 구글드라이브 마운트와 마찬가지로 아래의 경우, /static 경로에 접근할 수 있도록 설정해주는 것과 같다.
app.mount("/static", StaticFiles(directory="static"), name="static")

# OpenAI API 키는 .env 파일에서 관리합니다.
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o-mini")


# pydantic 의 BaseModel 객체를 상속받은 URLInput 객체
# URLInput 객체가 받는 url 은 str(문자형)으로 무조건 변환해서 받을 거임.
# 다시 말해 문자형으로 파싱한다는 의미.
class URLInput(BaseModel):
    url: str

# 마찬가지로 query 도 str 타입으로 파싱.
class QueryInput(BaseModel):
    query: str


# 전역 변수로 RAG 체인을 관리합니다.
rag_chain = None

# 사용자가 루트 디렉토리(홈페이지)에 접근했을때,index.html 화면을 보여줌.
# 이때, async 로 root를 감싸서 비동기 방식으로 처리된다.
@app.get("/")
async def root():
    return FileResponse("static/index.html")
# FileResponse 함수는 파일을 보여주도록 하는 메서드


@app.post("/process_url")
async def process_url(url_input: URLInput):
    global rag_chain # 전역변수로 선언되어있는 rag_chain 을 불러오기.
    try:
        loader = WebBaseLoader(
            web_paths=(url_input.url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(class_=("newsct_article _article_body",))
            ),
        )
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
        retriever = vectorstore.as_retriever()

        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        return {"message": "URL processed successfully"}
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in process_url: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query(query_input: QueryInput):
    global rag_chain
    if not rag_chain:
        raise HTTPException(status_code=400, detail="Please process a URL first")
    try:
        result = rag_chain.invoke({"input": query_input.query})
        return {"answer": result["answer"]}
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in query: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
