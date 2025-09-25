# delivery_agent.py
import asyncio
import os
import logging
import sys
# Docker 환경에서는 현재 디렉토리를 PYTHONPATH에 추가
sys.path.insert(0, '.')
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from utils.model_config import get_model_with_fallback

# 현재 폴더의 .env 파일 로드
load_dotenv()
from tools.redis_delivery_tools import (
    get_delivery_data,
    get_all_deliveries,
    get_completed_deliveries,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- 1. Agent 정의 ---
# Gemini 우선, 실패시 로컬 LLM 사용
try:
    model = get_model_with_fallback()
    logger.info(f"DeliveryAgent 모델 설정 완료: {type(model).__name__ if hasattr(model, '__class__') else model}")
except Exception as e:
    logger.error(f"DeliveryAgent 모델 설정 실패: {e}")
    # 최후의 fallback
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    model = LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434"
    )
    logger.info("DeliveryAgent 최후 fallback으로 로컬 LLM 사용")

root_agent = LlmAgent(
    model=model,
    name="DeliveryAgent",
    description="Redis에 저장된 배송 정보를 조회하는 에이전트 - Gemini/Local LLM hybrid",
    instruction="""너는 배송 관리 에이전트다.
    - 사용자가 주문번호를 말하면 반드시 get_delivery_data 툴을 호출해야 한다.
    - '모든 배송 데이터'를 원하면 get_all_deliveries 툴을 호출해야 한다.
    - '완료된 배송 수'를 물어보면 get_completed_deliveries 툴을 호출해야 한다.
    """,
    tools=[get_delivery_data, get_all_deliveries, get_completed_deliveries],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "simple_delivery_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

# --- 3. 실행 ---
async def main():
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: ORD1001 주문 상태 알려줘")
    final_response = "응답 없음"
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="ORD1001 주문 상태 알려줘")]
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_message,
    ):
        print(f"[DEBUG EVENT] {event}")  # 이벤트 구조 확인

        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    final_response = part.text
    
    if not final_response.strip():
        final_response = "응답 없음"

    print(f"<<< Agent Response: {final_response}")


if __name__ == "__main__":
    asyncio.run(main())   # 여기서는 에이전트 실행만
