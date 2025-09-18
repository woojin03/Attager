import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.adk import events
from google.genai import types

# redis 관련 툴 함수 불러오기
from ..tools.redis_quality_tools import (
    process_return_quality_check,
    process_recall_quality_check,
    manage_sellable_inventory,
    set_disposition_for_defect_items,
    record_defect_codes_and_metrics
)

# --- 1. Agent 정의 ---
quality_agent = LlmAgent(
    model=LiteLlm(model="ollama/mistral"),
    name="QualityAgent",
    description=(
        "반품·리콜 상품의 품질 검사를 수행하고 격리/처분을 결정하며, "
        "검사 결과에 따라 판매 가능 재고 상태를 관리합니다."
    ),
    instruction="""너는 품질 관리 에이전트다.
- '반품 상품 품질 검사'를 요청하면 process_return_quality_check 툴을 호출해야 한다.
- '리콜 상품 품질 검사'를 요청하면 process_recall_quality_check 툴을 호출해야 한다.
- '판매 가능 재고 상태 관리'를 요청하면 manage_sellable_inventory 툴을 호출해야 한다.
- '결함 상품 처분 결정'을 요청하면 set_disposition_for_defect_items 툴을 호출해야 한다.
- '결함 코드 기록'을 요청하면 record_defect_codes_and_metrics 툴을 호출해야 한다.
""",
    tools=[
        process_return_quality_check,
        process_recall_quality_check,
        manage_sellable_inventory,
        set_disposition_for_defect_items,
        record_defect_codes_and_metrics
    ],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "quality_management_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=quality_agent, app_name=APP_NAME, session_service=session_service)

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
