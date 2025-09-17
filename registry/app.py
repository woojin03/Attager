# app.py
import asyncio
import requests
from fastapi import FastAPI
from routes import register, discover, unregister
from storage import storage

app = FastAPI(title="Agent Registry")

# 라우터 등록
app.include_router(register.router)
app.include_router(discover.router)
app.include_router(unregister.router)

async def healthcheck_loop():
    """주기적으로 모든 Agent 헬스체크"""
    while True:
        for agent in storage.list_all():
            try:
                res = requests.get(f"{agent.endpoint}/health", timeout=2)
                if res.status_code != 200:
                    print(f"[WARN] {agent.name} unhealthy → 제거")
                    storage.unregister(agent.name)
            except Exception:
                print(f"[WARN] {agent.name} 응답 없음 → 제거")
                storage.unregister(agent.name)
        await asyncio.sleep(10)  # 10초마다 체크

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(healthcheck_loop())
