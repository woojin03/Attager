import redis
import json
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

def aggregate_agent_responses(agent_name: str, response_id: str, response_data: dict) -> dict:
    """여러 에이전트의 응답을 종합하여 저장합니다."""
    key = f"strategy:agent_response:{agent_name}:{response_id}"
    redis_client.set(key, json.dumps(response_data))
    return {"status": "success", "agent_name": agent_name, "response_id": response_id, "data": response_data}

def propose_new_dispatch_and_delivery_plan(plan_id: str, plan_details: dict) -> dict:
    """새로운 배차 및 배송 전략을 제안하고 저장합니다."""
    key = f"strategy:plan:{plan_id}"
    redis_client.set(key, json.dumps(plan_details))
    return {"status": "success", "plan_id": plan_id, "plan_details": plan_details}

def get_dispatch_and_delivery_plan(plan_id: str) -> dict:
    """특정 배차 및 배송 전략 계획을 조회합니다."""
    key = f"strategy:plan:{plan_id}"
    plan_data = redis_client.get(key)
    if plan_data:
        return {"status": "success", "plan_id": plan_id, "plan_details": json.loads(plan_data)}
    else:
        return {"status": "error", "message": f"Plan {plan_id} not found."}

def simulate_alternative_scenarios(scenario_id: str, scenario_data: dict) -> dict:
    """자원 부족/리콜 상황 등 대체 시뮬레이션을 수행하고 결과를 저장합니다."""
    key = f"strategy:simulation:{scenario_id}"
    redis_client.set(key, json.dumps(scenario_data))
    return {"status": "success", "scenario_id": scenario_id, "scenario_data": scenario_data}

def get_simulation_results(scenario_id: str) -> dict:
    """특정 시뮬레이션의 결과를 조회합니다."""
    key = f"strategy:simulation:{scenario_id}"
    simulation_data = redis_client.get(key)
    if simulation_data:
        return {"status": "success", "scenario_id": scenario_id, "simulation_data": json.loads(simulation_data)}
    else:
        return {"status": "error", "message": f"Simulation {scenario_id} not found."}

def analyze_reallocation_demand_effect(reallocation_plan_id: str, demand_data: dict) -> dict:
    """재고 재배치 후 수요 대응 효과를 분석하고 결과를 저장합니다."""
    analysis_key = f"strategy:reallocation_analysis:{reallocation_plan_id}"
    # This is a placeholder for complex demand forecasting and simulation logic.
    # For now, we'll simulate a simple effect.
    simulated_effect = {
        "reallocation_plan_id": reallocation_plan_id,
        "initial_demand_data": demand_data,
        "simulated_demand_response": "increased_efficiency", # Placeholder result
        "demand_met_percentage": 90 + (len(reallocation_plan_id) % 10) # Dummy calculation
    }
    redis_client.set(analysis_key, json.dumps(simulated_effect))
    return {"status": "success", "reallocation_plan_id": reallocation_plan_id, "analysis_result": simulated_effect}

def get_reallocation_analysis_results(reallocation_plan_id: str) -> dict:
    """특정 재배치 분석 결과를 조회합니다."""
    analysis_key = f"strategy:reallocation_analysis:{reallocation_plan_id}"
    analysis_data = redis_client.get(analysis_key)
    if analysis_data:
        return {"status": "success", "reallocation_plan_id": reallocation_plan_id, "analysis_results": json.loads(analysis_data)}
    else:
        return {"status": "error", "message": f"Reallocation analysis for {reallocation_plan_id} not found."}
