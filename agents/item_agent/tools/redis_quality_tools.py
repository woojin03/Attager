import redis
import os

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True
)

def process_return_quality_check(item_id: str, qc_result: str, disposition: str) -> dict:
    """반품 상품의 품질 검사를 수행하고 상태를 판정합니다.
    disposition: 'resell', 'discard', 'refurbish' 중 하나."""
    key = f"quality:return:{item_id}"
    redis_client.hset(key, mapping={
        "qc_result": qc_result,
        "disposition": disposition
    })
    return {"status": "success", "item_id": item_id, "qc_result": qc_result, "disposition": disposition}

def get_items_for_return_qc() -> list[str]:
    """품질 검사가 필요한 반품 상품 ID 리스트를 조회합니다."""
    # This is a placeholder. In a real system, this would query a queue or a list of pending items.
    # For now, let's assume some items are "pending_qc".
    # We'll use a simple pattern matching for demonstration.
    qc_pending_keys = redis_client.keys("quality:return:*:pending_qc")
    return [key.split(':')[2] for key in qc_pending_keys]

def get_return_item_disposition(item_id: str) -> dict:
    """주어진 item_id에 대한 반품 상품의 최종 처분(disposition)을 조회합니다."""
    key = f"quality:return:{item_id}"
    disposition = redis_client.hget(key, "disposition")
    if disposition:
        return {"status": "success", "item_id": item_id, "disposition": disposition}
    else:
        return {"status": "error", "message": f"Disposition for item {item_id} not found."}

def get_recall_items_list(product_id: str) -> dict:
    """특정 제품 ID에 대한 리콜 대상 상품 리스트를 추출합니다."""
    # This is a placeholder. In a real system, this would query a database or a specific recall list.
    # For demonstration, we'll assume recall items are marked with a pattern.
    recall_item_keys = redis_client.keys(f"quality:recall:{product_id}:*")
    item_ids = [key.split(':')[-1] for key in recall_item_keys]
    return {"status": "success", "product_id": product_id, "recall_items": item_ids}

def process_recall_quality_check(item_id: str, qc_result: str, isolation_status: str) -> dict:
    """리콜 상품의 품질 검사를 수행하고 격리/추적 상태를 업데이트합니다."""
    key = f"quality:recall:{item_id}"
    redis_client.hset(key, mapping={
        "qc_result": qc_result,
        "isolation_status": isolation_status
    })
    return {"status": "success", "item_id": item_id, "qc_result": qc_result, "isolation_status": isolation_status}

def manage_sellable_inventory(item_id: str, sellable_status: str) -> dict:
    """상품 ID에 따라 판매 가능/불가 상태를 전환하고 재고에 반영합니다."""
    key = f"item:id:{item_id}" # Assuming item status is in item agent's key
    if not redis_client.exists(key):
        return {"status": "error", "message": f"Item {item_id} does not exist."}
    redis_client.hset(key, "sellable_status", sellable_status)
    return {"status": "success", "item_id": item_id, "sellable_status": sellable_status}

def set_disposition_for_defect_items(item_id: str, disposition_action: str) -> dict:
    """결함 상품에 대한 재작업/폐기/재포장/재판매 등의 처분을 결정합니다."""
    key = f"quality:defect:{item_id}"
    redis_client.hset(key, "disposition_action", disposition_action)
    return {"status": "success", "item_id": item_id, "disposition_action": disposition_action}

def record_defect_codes_and_metrics(item_id: str, defect_code: str, metric_value: str) -> dict:
    """결함 코드를 기록하고 리포트 기초 데이터를 축적합니다."""
    key = f"quality:defect_log:{item_id}"
    redis_client.hset(key, mapping={
        "defect_code": defect_code,
        "metric_value": metric_value
    })
    return {"status": "success", "item_id": item_id, "defect_code": defect_code, "metric_value": metric_value}
