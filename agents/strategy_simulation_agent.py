import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.adk import events
from google.genai import types

# redis 관련 툴 함수 불러오기
from ..tools.redis_strategy_simulation_tools import (
    aggregate_agent_responses,
    propose_new_dispatch_and_delivery_plan,
    simulate_alternative_scenarios
)

# --- 1. Agent 정의 ---
strategy_simulation_agent = LlmAgent(
    model=LiteLlm(model="ollama/mistral"),
    name="StrategySimulationAgent",
    description=(
        "각 에이전트의 응답을 종합해 최적의 전략을 설계하고, "
        "차량 유지보수·배송·품질·입고 정보를 바탕으로 시뮬레이션을 수행합니다."
    ),
    instruction="""너는 전략 및 시뮬레이션 에이전트다.
- '에이전트 응답 종합'을 요청하면 aggregate_agent_responses 툴을 호출해야 한다.
- '새로운 배차 및 배송 전략 제안'을 요청하면 propose_new_dispatch_and_delivery_plan 툴을 호출해야 한다.
- '대체 시뮬레이션 수행'을 요청하면 simulate_alternative_scenarios 툴을 호출해야 한다.
""",
    tools=[
        aggregate_agent_responses,
        propose_new_dispatch_and_delivery_plan,
        simulate_alternative_scenarios
    ],
)

# --- 2. Runner + 세션 서비스 ---
APP_NAME = "strategy_simulation_app"
USER_ID = "user1"
SESSION_ID = "sess1"

session_service = InMemorySessionService()
runner = Runner(agent=strategy_simulation_agent, app_name=APP_NAME, session_service=session_service)

# --- 3. 실행 ---
async def main():
    # 세션 생성
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: 배송 에이전트 응답 종합해줘")

    final_response = "응답 없음"

    # Content/Part 객체 생성
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="배송 에이전트 응답 종합해줘")]
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
