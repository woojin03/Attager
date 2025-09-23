import logging

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import root_agent as vehicle_agent
from agent_executor import ADKAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10004)
def main(host, port):

    # Agent card (metadata)
    agent_card = AgentCard(
        name='Vehicle Agent',
        description=vehicle_agent.description,
        url=f'http://{host}:{port}',
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="vehicle_agent",
                name="read vehicle data",
                description="Read requested vehicle data from database",
                tags=["vehicle"],
                examples=[
                    "Read vehicle data for VEHICLE1001",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=vehicle_agent,
        ),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()