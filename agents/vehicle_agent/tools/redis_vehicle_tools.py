import redis
import os

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

def get_fleet_availability() -> dict:
    """전체 차량의 가용 현황을 요약하여 조회합니다."""
    available_vehicles = []
    on_delivery_vehicles = []
    maintenance_vehicles = []
    out_of_service_vehicles = []

    all_vehicle_keys = redis_client.keys("vehicle:id:*")
    for key in all_vehicle_keys:
        status = redis_client.hget(key, "status")
        if status == "available":
            available_vehicles.append(key)
        elif status == "on_delivery":
            on_delivery_vehicles.append(key)
        elif status == "maintenance":
            maintenance_vehicles.append(key)
        elif status == "out_of_service":
            out_of_service_vehicles.append(key)

    return {
        "status": "success",
        "available": len(available_vehicles),
        "on_delivery": len(on_delivery_vehicles),
        "maintenance": len(maintenance_vehicles),
        "out_of_service": len(out_of_service_vehicles),
        "total": len(all_vehicle_keys)
    }

def get_vehicles_on_maintenance() -> dict:
    """현재 정비 중인 차량 ID 리스트를 조회합니다."""
    maintenance_vehicles = []
    for key in redis_client.scan_iter("vehicle:id:*"):
        status = redis_client.hget(key, "status")
        if status == "maintenance":
            maintenance_vehicles.append(key.split(':')[-1]) # Extract vehicle ID
    return {"status": "success", "count": len(maintenance_vehicles), "vehicle_ids": maintenance_vehicles}


def get_vehicle_status(vehicle_id: str) -> dict:
    """단일 차량의 현재 상태를 조회합니다."""
    key = f"vehicle:id:{vehicle_id}"
    data = redis_client.hgetall(key)
    if not data:
        return {"status": "error", "message": f"No vehicle info found for {vehicle_id}"}
    return {"status": "success", "data": data}

def filter_available_vehicles() -> dict:
    """운행 가능한 차량(정비 중이거나 운행 불가 상태 제외)을 필터링하여 조회합니다."""
    available_vehicles = []
    for key in redis_client.scan_iter("vehicle:id:*"):
        status = redis_client.hget(key, "status")
        if status == "available" or status == "reserved": # Assuming reserved can also be considered available for assignment
            available_vehicles.append(key)
    return {"status": "success", "count": len(available_vehicles), "data": available_vehicles}

def reserve_vehicle_for_delivery(vehicle_id: str, delivery_id: str) -> dict:
    """특정 차량을 배송을 위해 배차/예약합니다."""
    key = f"vehicle:id:{vehicle_id}"
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Vehicle {vehicle_id} does not exist."}
    redis_client.hset(key, mapping={
        "status": "reserved",
        "current_delivery_id": delivery_id
    })
    return {"status": "success", "vehicle_id": vehicle_id, "delivery_id": delivery_id, "new_status": "reserved"}

def release_vehicle_reservation(vehicle_id: str) -> dict:
    """배차된 차량의 예약을 해제/반납합니다."""
    key = f"vehicle:id:{vehicle_id}"
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Vehicle {vehicle_id} does not exist."}
    redis_client.hset(key, "status", "available")
    redis_client.hdel(key, "current_delivery_id")
    return {"status": "success", "vehicle_id": vehicle_id, "new_status": "available"}

def update_vehicle_operation_status(vehicle_id: str, new_status: str) -> dict:
    """차량의 운행 상태를 업데이트합니다 (예: on_delivery, idle, maintenance, out_of_service)."""
    key = f"vehicle:id:{vehicle_id}"
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Vehicle {vehicle_id} does not exist."}
    redis_client.hset(key, "status", new_status)
    return {"status": "success", "vehicle_id": vehicle_id, "new_status": new_status}

def schedule_vehicle_maintenance(vehicle_id: str, maintenance_date: str, description: str) -> dict:
    """차량 정비 일정을 등록하고 반영합니다."""
    key = f"vehicle:maintenance:{vehicle_id}"
    redis_client.hset(key, mapping={
        "maintenance_date": maintenance_date,
        "description": description,
        "status": "scheduled"
    })
    # Update vehicle status to maintenance if it's not already
    vehicle_key = f"vehicle:id:{vehicle_id}"
    if redis_client.exists(vehicle_key) and redis_client.hget(vehicle_key, "status") != "out_of_service":
        redis_client.hset(vehicle_key, "status", "maintenance")
    return {"status": "success", "vehicle_id": vehicle_id, "maintenance_date": maintenance_date, "description": description}

def assign_recall_vehicles(vehicle_id: str, recall_id: str) -> dict:
    """리콜 상품 회수 전용 차량을 배정합니다."""
    key = f"vehicle:id:{vehicle_id}"
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Vehicle {vehicle_id} does not exist."}
    redis_client.hset(key, mapping={
        "status": "assigned_for_recall",
        "current_recall_id": recall_id
    })
    return {"status": "success", "vehicle_id": vehicle_id, "recall_id": recall_id, "new_status": "assigned_for_recall"}

def get_assigned_recall_vehicles(recall_id: str) -> dict:
    """특정 리콜에 배정된 차량 리스트를 조회합니다."""
    assigned_vehicles = []
    for key in redis_client.scan_iter("vehicle:id:*"):
        data = redis_client.hgetall(key)
        if data.get("status") == "assigned_for_recall" and data.get("current_recall_id") == recall_id:
            assigned_vehicles.append(key.split(':')[-1])
    return {"status": "success", "recall_id": recall_id, "assigned_vehicles": assigned_vehicles}

def update_recall_vehicle_status(vehicle_id: str, new_status: str) -> dict:
    """리콜 배정 차량의 상태를 업데이트합니다."""
    key = f"vehicle:id:{vehicle_id}"
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Vehicle {vehicle_id} does not exist."}
    redis_client.hset(key, "status", new_status)
    return {"status": "success", "vehicle_id": vehicle_id, "new_status": new_status}

def get_vehicle_capacity(vehicle_id: str) -> dict:
    """차량의 적재 용량을 조회합니다."""
    key = f"vehicle:id:{vehicle_id}"
    capacity = redis_client.hget(key, "capacity")
    if capacity is None:
        return {"status": "error", "message": f"Capacity info not found for {vehicle_id}"}
    return {"status": "success", "vehicle_id": vehicle_id, "capacity": int(capacity)}

def recommend_optimal_vehicles(origin: str, destination: str, required_capacity: int) -> dict:
    """출발지, 목적지, 필요한 적재 용량을 기반으로 최적 차량을 추천합니다."""
    # This is a simplified recommendation logic. A real system would involve:
    # 1. Geospatial calculations for distance and route optimization.
    # 2. Real-time traffic data.
    # 3. More sophisticated vehicle matching (e.g., vehicle type, special requirements).
    
    # For simulation, we'll iterate through available vehicles and check capacity.
    recommended_vehicles = []
    for key in redis_client.scan_iter("vehicle:id:*"):
        vehicle_data = redis_client.hgetall(key)
        if vehicle_data.get("status") == "available" and int(vehicle_data.get("capacity", 0)) >= required_capacity:
            # Dummy distance calculation. In reality, this would be route-based.
            vehicle_id = key.split(':')[-1]
            distance = abs(hash(origin) - hash(destination)) % 1000 # Placeholder distance
            recommended_vehicles.append({
                "vehicle_id": vehicle_id,
                "capacity": int(vehicle_data["capacity"]),
                "distance_to_destination": distance # Simplified
            })
    
    # Sort by distance (closest first)
    recommended_vehicles.sort(key=lambda x: x["distance_to_destination"])
    
    return {"status": "success", "origin": origin, "destination": destination, "required_capacity": required_capacity, "recommended_vehicles": recommended_vehicles}
