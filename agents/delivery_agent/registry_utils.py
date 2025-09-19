# registry_utils.py
import requests
from google.adk.agents import LlmAgent

def register_to_registry(agent: LlmAgent, endpoint: str, tags: list[str]):
    """레지스트리 서버에 AgentCard 등록"""
    card = {
        "name": agent.name,
        "description": agent.description,
        "endpoint": endpoint,
        "tags": tags,
    }
    try:
        res = requests.post("http://127.0.0.1:9000/register", json=card, timeout=3)
        if res.status_code == 200:
            print(f"[INFO] Agent {card['name']} 등록 성공")
        else:
            print(f"[WARN] 등록 실패: {res.status_code} {res.text}")
    except Exception as e:
        print(f"[ERROR] 레지스트리 서버 연결 실패: {e}")
