# delivery_agent_server.py
from fastapi import FastAPI
from delivery_agent import root_agent, runner, session_service, APP_NAME, USER_ID, SESSION_ID
from delivery_agent import register_to_registry
from google.genai import types
import asyncio


app = FastAPI()

@app.on_event("startup")
def startup_event():
    # 서버 시작 시 레지스트리에 등록
    register_to_registry(root_agent, "http://127.0.0.1:8001", ["delivery", "redis"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
async def run_agent(user_input: str):
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    final_response = "응답 없음"
    user_message = types.Content(role="user", parts=[types.Part(text=user_input)])

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text

    return {"response": final_response}
