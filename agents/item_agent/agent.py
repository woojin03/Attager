import asyncio
import os
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

# redis 관련 툴 함수 불러오기
from tools.redis_item_tools import (
    get_item_details,
    track_item_inventory,
    # update_item_status,
)

# --- 1. Agent 정의 ---
ollama_host = os.getenv("OLLAMA_HOST", "localhost")
root_agent = LlmAgent(
    model=LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434"
    ),
    name="ItemAgent",
    description=(
        "상품 정보를 관리하고, 재고를 추적하며, 상품 관련 작업을 처리합니다."
    ),
    instruction="""너는 상품 관리 에이전트다.
    - 사용자가 상품 ID를 말하면 반드시 get_item_details 툴을 호출해야 한다.
    - '재고 수량'을 물어보면 track_item_inventory 툴을 호출해야 한다.
    """, # - '상품 상태 업데이트'를 요청하면 update_item_status 툴을 호출해야 한다.
    tools=[
        get_item_details,
        track_item_inventory,
        # update_item_status,
    ],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "item_management_app"
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

    print(">>> User Input: ITEM001 상품 상세 정보 알려줘")

    final_response = "응답 없음"

    # Content/Part 객체 생성
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="ITEM001 상품 상세 정보 알려줘")]
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
