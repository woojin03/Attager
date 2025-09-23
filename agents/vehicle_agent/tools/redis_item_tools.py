# /home/agents/tools/redis_tools.py
import redis
import os

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

def get_item_details(item_id: str, warehouse_id: str = None) -> dict:
    """상품 ID로 상품 상세 정보 조회 (특정 창고 지정 가능)"""
    key = f"item:{warehouse_id}:{item_id}" if warehouse_id else f"item:id:{item_id}"
    data = redis_client.hgetall(key)
    if not data:
        return {"status": "error", "message": f"No item info found for {item_id} in warehouse {warehouse_id}" if warehouse_id else f"No item info found for {item_id}"}
    return {"status": "success", "data": data}

def track_item_inventory(item_id: str, warehouse_id: str = None) -> dict:
    """상품 ID로 재고 수량 조회 (특정 창고 지정 가능)"""
    key = f"item:{warehouse_id}:{item_id}" if warehouse_id else f"item:id:{item_id}"
    inventory = redis_client.hget(key, "inventory")
    if inventory is None:
        return {"status": "error", "message": f"Inventory info not found for {item_id} in warehouse {warehouse_id}" if warehouse_id else f"Inventory info not found for {item_id}"}
    return {"status": "success", "item_id": item_id, "inventory": int(inventory), "warehouse_id": warehouse_id}

def update_warehouse_inventory(item_id: str, warehouse_id: str, quantity: int) -> dict:
    """특정 창고의 상품 재고를 업데이트합니다."""
    key = f"item:{warehouse_id}:{item_id}"
    # Use hincrby to increment or decrement the inventory safely
    new_inventory = redis_client.hincrby(key, "inventory", quantity)
    return {"status": "success", "item_id": item_id, "warehouse_id": warehouse_id, "new_inventory": new_inventory}

def get_all_warehouse_inventories_for_item(item_id: str) -> dict:
    """특정 상품에 대한 모든 창고의 재고 현황을 조회합니다."""
    inventories = {}
    # Assuming item keys follow a pattern like item:warehouse_id:item_id
    search_pattern = f"item:*: {item_id}"
    for key in redis_client.scan_iter(search_pattern):
        warehouse_id = key.split(':')[1]
        inventory = redis_client.hget(key, "inventory")
        if inventory:
            inventories[warehouse_id] = int(inventory)
    return {"status": "success", "item_id": item_id, "inventories": inventories}

def get_all_warehouse_ids() -> list[str]:
    """모든 창고 ID 리스트를 조회합니다."""
    # This is a placeholder. In a real system, warehouse IDs would be managed more robustly.
    # For now, we'll extract them from item keys.
    warehouse_ids = set()
    for key in redis_client.scan_iter("item:*:*"):
        parts = key.split(':')
        if len(parts) > 1:
            warehouse_ids.add(parts[1])
    return list(warehouse_ids)

def get_total_inventory_by_item_id(item_id: str) -> dict:
    """특정 상품 ID에 대한 전체 창고의 재고 합계를 조회합니다."""
    total_inventory = 0
    # Assuming item keys follow a pattern like item:warehouse_id:item_id
    # We need to find all keys related to this item_id across all warehouses
    # This might be inefficient for very large datasets, consider a dedicated index if performance is critical
    search_pattern = f"item:*: {item_id}"
    for key in redis_client.scan_iter(search_pattern):
        inventory = redis_client.hget(key, "inventory")
        if inventory:
            total_inventory += int(inventory)
    return {"status": "success", "item_id": item_id, "total_inventory": total_inventory}

def get_recall_item_inventory_by_warehouse(item_id: str, warehouse_id: str) -> dict:
    """특정 창고에서 리콜 대상 상품의 재고를 파악합니다."""
    key = f"item:{warehouse_id}:{item_id}"
    inventory = redis_client.hget(key, "inventory")
    # In a real scenario, you might also check a 'is_recalled' flag or similar
    if inventory is None:
        return {"status": "error", "message": f"Inventory info not found for {item_id} in warehouse {warehouse_id}"}
    return {"status": "success", "item_id": item_id, "warehouse_id": warehouse_id, "inventory": int(inventory)}

def update_item_status(item_id: str, status: str) -> dict:
    """상품 ID로 상품 상태 업데이트"""
    key = f"item:id:{item_id}"
    # Check if item exists before updating
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Item {item_id} does not exist."}
    redis_client.hset(key, "status", status)
    return {"status": "success", "item_id": item_id, "new_status": status}
