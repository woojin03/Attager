import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.adk import events
from google.genai import types

# redis 관련 툴 함수 불러오기
from ..tools.redis_vehicle_tools import (
    get_fleet_availability,
    get_vehicle_status,
    filter_available_vehicles,
    reserve_vehicle_for_delivery,
    release_vehicle_reservation,
    update_vehicle_operation_status,
    schedule_vehicle_maintenance,
    assign_recall_vehicles
)

# --- 1. Agent 정의 ---
vehicle_agent = LlmAgent(
    model=LiteLlm(model="ollama/mistral"),
    name="VehicleAgent",
    description=(
        "운행가능 차량과 배송 투입 차량의 가용 여부 및 운행 상태를 관리합니다. "
        "차량 상태 조회/업데이트, 배정·해제, 정비 스케줄 반영을 수행합니다."
    ),
    instruction="""너는 배차/차량 운영 에이전트다.
- '전체 가용 현황'을 요청하면 get_fleet_availability 툴을 호출해야 한다.
- '차량 상태 조회'를 요청하면 get_vehicle_status 툴을 호출해야 한다.
- '운행 가능 차량 필터링'을 요청하면 filter_available_vehicles 툴을 호출해야 한다.
- '배차/예약'을 요청하면 reserve_vehicle_for_delivery 툴을 호출해야 한다.
- '배차 해제/반납'을 요청하면 release_vehicle_reservation 툴을 호출해야 한다.
- '운행 상태 업데이트'를 요청하면 update_vehicle_operation_status 툴을 호출해야 한다.
- '정비 일정 등록/반영'을 요청하면 schedule_vehicle_maintenance 툴을 호출해야 한다.
- '리콜 회수 전용 차량 배정'을 요청하면 assign_recall_vehicles 툴을 호출해야 한다.
""",
    tools=[
        get_fleet_availability,
        get_vehicle_status,
        filter_available_vehicles,
        reserve_vehicle_for_delivery,
        release_vehicle_reservation,
        update_vehicle_operation_status,
        schedule_vehicle_maintenance,
        assign_recall_vehicles
    ],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "vehicle_management_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=vehicle_agent, app_name=APP_NAME, session_service=session_service)

# --- 3. 실행 ---
async def main():
    # 세션 생성
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: 전체 차량 가용 현황 알려줘")

    final_response = "응답 없음"

    # Content/Part 객체 생성
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="전체 차량 가용 현황 알려줘")]
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
