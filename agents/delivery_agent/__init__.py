from .agent import root_agent, runner, session_service, APP_NAME, USER_ID, SESSION_ID
from .registry_utils import register_to_registry

register_to_registry(root_agent, endpoint="http://127.0.0.1:8001", tags=["delivery", "redis"])
