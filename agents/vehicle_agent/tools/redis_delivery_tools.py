# /home/agents/tools/redis_tools.py
import redis
import json
import os

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

def get_delivery_data(order_id: str) -> dict:
    """주문 ID로 배송 상세 조회"""
    key = f"delivery:order:{order_id}"
    data = redis_client.hgetall(key)
    if not data:
        return {"status": "error", "message": f"No delivery info found for {order_id}"}
    return {"status": "success", "data": data}

def get_all_deliveries() -> dict:
    """Redis에 저장된 모든 배송 데이터를 가져오기"""
    deliveries = []
    for key in redis_client.scan_iter("delivery:order:*"):
        data = redis_client.hgetall(key)
        if data:
            deliveries.append(data)
    return {"status": "success", "count": len(deliveries), "data": deliveries}

def get_completed_deliveries() -> dict:
    """배송 상태가 completed 인 주문 개수 세기"""
    deliveries = []
    for key in redis_client.scan_iter("delivery:order:*"):
        data = redis_client.hgetall(key)
        if data.get("status") == "completed":
            deliveries.append(data)
    return {"status": "success", "completed_count": len(deliveries), "data": deliveries}

def create_redelivery_request(original_order_id: str, item_id: str, delivery_type: str, customer_info: dict) -> dict:
    """리퍼브나 교환 대상 상품에 대한 재배송 요청을 생성합니다.
    delivery_type: 'refurbish' 또는 'exchange'."""
    # In a real system, this would involve more complex logic, including generating a new order ID,
    # checking inventory, scheduling, etc. For now, we'll just log the request.
    redelivery_key = f"redelivery:request:{original_order_id}:{item_id}"
    request_data = {
        "original_order_id": original_order_id,
        "item_id": item_id,
        "delivery_type": delivery_type,
        "customer_name": customer_info.get("name"),
        "customer_address": customer_info.get("address"),
        "status": "pending"
    }
    redis_client.hset(redelivery_key, mapping=request_data)
    return {"status": "success", "message": "Redelivery request created", "request_id": redelivery_key}

def get_redelivery_request_status(original_order_id: str, item_id: str) -> dict:
    """특정 재배송 요청의 상태를 조회합니다."""
    redelivery_key = f"redelivery:request:{original_order_id}:{item_id}"
    data = redis_client.hgetall(redelivery_key)
    if not data:
        return {"status": "error", "message": f"Redelivery request for {original_order_id}/{item_id} not found."}
    return {"status": "success", "data": data}

def update_delivery_route(delivery_id: str, new_route: str) -> dict:
    """주어진 배송 ID의 배송 경로를 업데이트합니다. new_route는 쉼표로 구분된 위치 목록입니다."""
    delivery_key = f"delivery:order:{delivery_id}"
    if not redis_client.exists(delivery_key):
        return {"status": "error", "message": f"Delivery {delivery_id} not found."}
    
    # 쉼표로 구분된 문자열을 리스트로 변환
    route_list = [location.strip() for location in new_route.split(",") if location.strip()]
    redis_client.hset(delivery_key, "route", json.dumps(route_list))
    return {"status": "success", "delivery_id": delivery_id, "new_route": route_list}

def calculate_eta(origin: str, destination: str, vehicle_type: str) -> dict:
    """출발지, 목적지, 차량 유형을 기반으로 예상 도착 시간을 산출합니다."""
    # This would involve a complex geospatial and traffic analysis in a real system.
    # For this simulation, we'll use a placeholder logic.
    distance = abs(hash(origin) - hash(destination)) % 1000 # Dummy distance
    speed_factor = {"truck": 60, "van": 80, "motorcycle": 100}.get(vehicle_type, 70) # km/h
    eta_hours = distance / speed_factor
    return {"status": "success", "origin": origin, "destination": destination, "eta_hours": round(eta_hours, 2)}

def create_recall_collection_schedule(recall_id: str, item_id: str, customer_info: dict, collection_date: str) -> dict:
    """리콜 상품 회수를 위한 고객 대상 배송 일정을 생성합니다."""
    collection_key = f"recall:collection:{recall_id}:{item_id}"
    schedule_data = {
        "recall_id": recall_id,
        "item_id": item_id,
        "customer_name": customer_info.get("name"),
        "customer_address": customer_info.get("address"),
        "collection_date": collection_date,
        "status": "scheduled"
    }
    redis_client.hset(collection_key, mapping=schedule_data)
    return {"status": "success", "message": "Recall collection schedule created", "collection_key": collection_key}

def get_recall_collection_schedule(recall_id: str, item_id: str) -> dict:
    """특정 리콜 상품 회수 일정을 조회합니다."""
    collection_key = f"recall:collection:{recall_id}:{item_id}"
    data = redis_client.hgetall(collection_key)
    if not data:
        return {"status": "error", "message": f"Recall collection schedule for {recall_id}/{item_id} not found."}
    return {"status": "success", "data": data}