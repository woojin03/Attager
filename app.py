# /home/agents/app.py
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 서브 에이전트 불러오기
from delivery_agent.root_agent import root_agent # 경로 확인 필요!

import argparse

APP_NAME = "logistics_app"
USER_ID = "admin"
SESSION_ID = "sess1"

def get_agent_by_name(agent_name: str):
    if agent_name == "delivery_agent":
        return root_agent
    # Add other agents here as needed
    return root_agent

async def main():
    parser = argparse.ArgumentParser(description="Run an ADK agent on a specified port.")
    parser.add_argument("--agent", type=str, default="delivery_agent",
                        help="Name of the agent to run (e.g., delivery_agent)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port number to run the agent on")
    args = parser.parse_args()

    selected_agent = get_agent_by_name(args.agent)

    # 세션 서비스 & 러너 준비
    session_service = InMemorySessionService()
    runner = Runner(agent=selected_agent, app_name=APP_NAME, session_service=session_service)

    # 세션 생성
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(">>> User Input: ORD1001 주문 상태 알려줘")
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="ORD1001 주문 상태 알려줘")]
    )

    final_response = "응답 없음"

    # 러너 실행
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
