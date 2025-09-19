# README.md

## A2A Sample Project

이 프로젝트는 Google ADK 기반으로 동작하는 **멀티 에이전트 시스템** 샘플입니다.  
- `agents/` : 실제 ADK 기반 에이전트들이 구현된 디렉토리  
- `registry/` : 에이전트 등록/탐색을 위한 레지스트리 서버  
- `agentDB/` : Redis 등 백엔드 스토리지를 도커 컴포즈로 실행  

## 📦 사전 준비
- Python 3.12+
- Docker & Docker Compose
- Linux/WSL 환경 권장

## 🚀 실행 방법

### 1. 데이터베이스 실행
```bash
cd agentDB
docker compose up -d
```

### 2. 가상환경 생성 및 의존성 설치
```bash
cd ../a2a-sample
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 에이전트 실행

#### (1) ADK UI로 에이전트 확인
```bash
cd agents
adk web
```
👉 브라우저: http://127.0.0.1:8000/dev-ui
👉 또는 http://127.0.0.1:8000 에 접속하여 Agent 입력 후 대답 확인 가능

#### (2) FastAPI 기반 에이전트 서버 실행 (에이전트 카드 등록용)
```bash
uvicorn delivery_agent.delivery_agent_server:app --port 8001
```
👉 /health, /run 엔드포인트 제공

### 4. 레지스트리 서버 실행
```bash
cd ../registry
uv run uvicorn app:app --reload --port 9000
```
👉 브라우저: http://127.0.0.1:9000/agents

## 📡 주요 엔드포인트

### 에이전트 서버 (delivery_agent)
- `GET /health` : 상태 확인
- `POST /run`   : 사용자 입력 실행

### 레지스트리 서버 (registry)
- `POST   /register`            : 에이전트 등록
- `GET    /agents`              : 등록된 에이전트 목록 조회
- `DELETE /unregister/{name}`   : 에이전트 해제

## 🛠️ 개발 노트
- `delivery_agent` 패키지는 `root_agent`와 `Runner`를 정의하고,
  FastAPI 서버(`delivery_agent_server.py`)를 통해 외부에 노출합니다.
- 레지스트리 서버(`registry/app.py`)는 주기적으로 `/health` 체크 후
  응답 없는 에이전트를 자동 제거합니다.

## 📂 폴더 구조
```
a2a-sample/
├── agentDB/
│   └── docker-compose.yml
├── agents/
│   ├── delivery_agent/
│   │   ├── __init__.py
│   │   ├── delivery_agent.py
│   │   ├── delivery_agent_server.py
│   │   └── registry_utils.py
│   └── tools/
│       └── redis_delivery_tools.py
├── registry/
│   ├── app.py
│   ├── models.py
│   ├── routes/
│   │   ├── register.py
│   │   ├── discover.py
│   │   └── unregister.py
│   └── storage.py
├── requirements.txt
└── README.md
```

## ✅ 실행 순서 요약
1. `agentDB` → `docker compose up -d`
2. `a2a-sample` → 가상환경 생성 + `pip install -r requirements.txt`
3. `agents` → `adk web` (UI 확인: `http://127.0.0.1:8000`)
           `uvicorn delivery_agent.delivery_agent_server:app --port 8001` (에이전트 서버 실행)
4. `registry` → `uv run uvicorn app:app --reload --port 9000` (레지스트리 서버 실행)

## 🔍 확인 방법

### 1) 레지스트리 서버 실행 후:
```bash
curl http://127.0.0.1:9000/agents
```
👉 등록된 `SimpleDeliveryAgent` 확인 가능

### 2) ADK UI 실행 후:
- 브라우저에서 `http://127.0.0.1:8000` 접속
- "ORD1001 주문 상태 알려줘" 입력
- Agent가 Redis에서 데이터를 조회 후 응답 반환