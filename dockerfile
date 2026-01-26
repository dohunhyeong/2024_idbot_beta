# Python 3.11 slim 버전 사용
FROM python:3.11-slim

# 환경 변수 설정 (로그 버퍼링 방지)
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    PYTHONPATH=/app

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Poetry 공식 설치 스크립트 사용 (더 안정적)
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

# Poetry 경로 설정
ENV PATH="/root/.local/bin:$PATH"

# 의존성 파일 복사 (캐시 최적화)
COPY pyproject.toml poetry.lock ./

# Poetry 설정 후 의존성 설치 (프로덕션 패키지만 설치)
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# 앱 코드 복사 (최적화)
COPY . .

# 포트 노출
EXPOSE 8000

# 컨테이너 실행 시 사용할 명령어 (exec 방식 보장)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]