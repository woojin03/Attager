import os
import json
import uvicorn
import logging
import httpx
import os
import uuid
import json
from typing import Any
from a2a.types import AgentCard
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    SendMessageResponse,
    MessageSendParams
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- 1. AgentCard 로더 ---

def load_agent_cards(tool_context: ToolContext) -> list[str]:
    """agent_cards 폴더의 JSON을 읽고 state에 저장, 에이전트 이름 리스트 반환"""
    cards = {}
    base_dir = "./agent_cards"
    for fname in os.listdir(base_dir):
        with open(os.path.join(base_dir, fname), "r", encoding="utf-8") as f:
                content = f.read()
                # 환경변수 치환
                content = content.replace("${DELIVERY_AGENT_HOST:-localhost}", os.getenv("DELIVERY_AGENT_HOST", "localhost"))
                content = content.replace("${ITEM_AGENT_HOST:-localhost}", os.getenv("ITEM_AGENT_HOST", "localhost"))
                content = content.replace("${QUALITY_AGENT_HOST:-localhost}", os.getenv("QUALITY_AGENT_HOST", "localhost"))
                content = content.replace("${VEHICLE_AGENT_HOST:-localhost}", os.getenv("VEHICLE_AGENT_HOST", "localhost"))
                
                data = json.loads(content)
                if hasattr(AgentCard, "model_validate"):   # pydantic v2
                    card = AgentCard.model_validate(data)
                else:  # pydantic v1
                    card = AgentCard.parse_obj(data)
                name = card.name or fname.replace(".json", "")
                cards[name] = card
    tool_context.state["cards"] = cards
    return list(cards.keys())

# --- 2. Remote Agent 호출 ---

async def call_remote_agent(tool_context, agent_name: str, task: str) -> dict:
    """agent_name으로 카드 조회 후 원격 호출 (A2AClient 사용)"""
    cards = tool_context.state.get("cards", {})
    card: AgentCard = cards.get(agent_name)
    if not card:
        return {"error": f"Agent {agent_name} not found"}

    message_id = uuid.uuid4().hex
    agent_url = card.url  # AgentCard에 정의된 URL 사용
    send_message_payload: dict[str, Any] = {
        "message": {
            "role": "user",
            "parts": [
                {"type": "text", "text": task}
            ],
            "messageId": message_id,
        },
    }
    async with httpx.AsyncClient(timeout=600) as http_client:
        client = A2AClient(http_client, card, url=agent_url)
        message_request = SendMessageRequest(id=message_id, params=MessageSendParams(**send_message_payload))
        response: SendMessageResponse = await client.send_message(message_request)
        return response.model_dump()  # dict로 변환해서 반환

# --- 3. 응답 집계 ---
def aggregate_responses(tool_context: ToolContext, responses: list) -> str:
    """아무 타입이 들어와도 문자열로 합쳐서 반환"""
    return "\n".join(str(r) for r in responses)

def return_result(tool_context: ToolContext, result: str) -> str:
    """
    최종 결과를 사용자에게 전달하는 도구.
    이 도구를 호출하면 더 이상 다른 도구를 호출하지 않고,
    LLM이 이 결과를 최종 응답으로 반환한다.
    """
    # state에 저장해둘 수도 있음 (선택 사항)
    tool_context.state["final_result"] = result
    return result

# --- Root Agent 정의 ---
ollama_host = os.getenv("OLLAMA_HOST", "localhost")
model = LiteLlm(
    model="ollama_chat/gpt-oss:20b",
    api_base=f"http://{ollama_host}:11434",
    temperature=0.7,
)

root_agent = LlmAgent(
    name="root_orchestrator",
    model=model,
    instruction=(
        "너는 Root Orchestrator Agent야.\n"
        "너의 임무는 사용자 요청에 맞는 에이전트를 선택해서 작업을 위임하고 결과를 집계해서 사용자에게 반환하는 것이야.\n"
        "'load_agent_cards'는 에이전트 카드를 불러오는 도구이다\n"
        "'call_remote_agent'는 에이전트를 호출하는 도구이다\n"
        "   (에이전트 카드에서 agent_name과 task를 파라미터로 넣어 호출해야 한다)\n"
        "'aggregate_responses'는 에이전트의 응답을 합치는 도구이다\n"
        "'return_result'에는 너가 사용자에게 응답할 내용을 적고 사용자에게 반환해\n"
    ),
    description="LLM 기반 Root Orchestrator Agent (multi-agent coordination)",
    tools=[FunctionTool(load_agent_cards), FunctionTool(call_remote_agent), FunctionTool(aggregate_responses), FunctionTool(return_result)],
)

# --- A2A 서버로 노출 ---
app = to_a2a(root_agent, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
