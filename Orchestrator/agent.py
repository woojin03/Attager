import os
import json
import uvicorn
import logging
import httpx
import os
import uuid
import json
from typing import Any, List
from a2a.types import AgentCard
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Message,
    Role,
    Part,
    TextPart,
    SendMessageRequest,
    SendMessageResponse,
    MessageSendParams,
    TransportProtocol,
    Task
)
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from remote_agent_connection import RemoteAgentConnections
import sys
# Docker 환경에서는 현재 디렉토리를 PYTHONPATH에 추가
sys.path.insert(0, '.')
from utils.model_config import get_model_with_fallback

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

CONNECTIONS: dict[str, RemoteAgentConnections] = {}

async def call_remote_agent(tool_context: ToolContext, agent_name: str, task: str):
    """원격 에이전트 호출 (connections는 전역 dict 관리)."""
    try:
        state = tool_context.state

        # 1. 카드 조회
        cards: dict[str, AgentCard] = state.get("cards", {})
        card: AgentCard = cards.get(agent_name)
        if not card:
            return {"error": f"Agent {agent_name} not found"}

        # 2. 전역 CONNECTIONS 조회
        client = CONNECTIONS.get(agent_name)
        if not client:
            http_client = httpx.AsyncClient(timeout=30)
            config = ClientConfig(
                httpx_client=http_client,
                supported_transports=[TransportProtocol.jsonrpc],  # 강제
            )
            client_factory = ClientFactory(config)
            client = RemoteAgentConnections(client_factory, card)
            CONNECTIONS[agent_name] = client
            logger.debug(f"[call_remote_agent] RemoteAgentConnections 생성: {agent_name}")

        # 3. ID 관리
        message_id = state.get("message_id") or str(uuid.uuid4())
        context_id = state.get("context_id")
        task_id = state.get("task_id")

        request_message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=task))],
            message_id=message_id,
            context_id=context_id,
            task_id=task_id,
        )

        # 4. 메시지 전송
        response = await client.send_message(request_message)

        # 5. 응답 처리
        if isinstance(response, Message):
            content = " ".join(
                p.root.text for p in response.parts if hasattr(p.root, "text")
            )
            return {"type": "message", "content": content}

        elif isinstance(response, Task):
            result_dict = {
                "type": "task",
                "task_id": response.id,
                "state": response.status.state.value if response.status else None,
            }
            if response.status and response.status.message:
                result_dict["message"] = " ".join(
                    p.root.text for p in response.status.message.parts if hasattr(p.root, "text")
                )
            if response.artifacts:
                result_dict["artifacts"] = [
                    " ".join(
                        p.root.text for p in artifact.parts if hasattr(p.root, "text")
                    )
                    for artifact in response.artifacts
                ]
            return result_dict

        else:
            return {"error": f"Unexpected result type: {type(response)}"}

    except Exception as e:
        logger.exception("[call_remote_agent] 실행 오류")
        return {"error": str(e)}


# --- 3. 응답 집계 ---
def aggregate_responses(tool_context: ToolContext, response1: str = "", response2: str = "", response3: str = "", response4: str = "", response5: str = "") -> str:
    """여러 에이전트 응답을 문자열로 합쳐서 반환 (최대 5개)"""
    responses = [r for r in [response1, response2, response3, response4, response5] if r.strip()]
    return "\n".join(responses)

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
# Gemini 우선, 실패시 로컬 LLM 사용
try:
    model = get_model_with_fallback()
    logger.info(f"모델 설정 완료: {type(model).__name__ if hasattr(model, '__class__') else model}")
except Exception as e:
    logger.error(f"모델 설정 실패: {e}")
    # 최후의 fallback
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    model = LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434",
        temperature=0.7,
    )
    logger.info("최후 fallback으로 로컬 LLM 사용")

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
    description="LLM 기반 Root Orchestrator Agent (multi-agent coordination) - Gemini/Local LLM hybrid",
    tools=[FunctionTool(load_agent_cards), FunctionTool(call_remote_agent), FunctionTool(aggregate_responses), FunctionTool(return_result)],
)

