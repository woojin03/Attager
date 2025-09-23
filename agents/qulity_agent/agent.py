import asyncio
import os
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

# redis 관련 툴 함수 불러오기
from tools.redis_quality_tools import (
    get_items_for_return_qc,
    get_return_item_disposition,
    get_recall_items_list,
)   

# --- 1. Agent 정의 ---
ollama_host = os.getenv("OLLAMA_HOST", "localhost")
root_agent = LlmAgent(
    model=LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434"
    ),
    name="QualityAgent",
    description=(
        "반품·리콜 상품의 품질 검사를 수행하고 격리/처분을 결정하며, "
        "검사 결과에 따라 판매 가능 재고 상태를 관리합니다."
    ),
    instruction="""너는 품질 관리 에이전트다.\
    - '품질 검사가 필요한 반품 상품'을 요청하면 get_items_for_return_qc 툴을 호출해야 한다.\
    - '반품 상품의 최종 처분'을 조회하려면 get_return_item_disposition 툴을 호출해야 한다.\
    - '특정 제품 ID의 리콜 대상 상품 리스트'를 요청하면 get_recall_items_list 툴을 호출해야 한다.
    """,
    tools=[
        get_items_for_return_qc,
        get_return_item_disposition,
        get_recall_items_list,
    ],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "quality_management_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

# --- 3. 실행 ---
async def main():
    # 세션 생성
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: 반품 상품 ITEM002 품질 검사 결과 good, 처분 재판매로 해줘")

    final_response = "응답 없음"

    # Content/Part 객체 생성
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="반품 상품 ITEM002 품질 검사 결과 good, 처분 재판매로 해줘")]
    )

    # run_async 호출
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text

    print(f"<<< Agent Response: {final_response}")



if __name__ == "__main__":
    asyncio.run(main())
