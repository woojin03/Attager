import random
import datetime
import os

# 데이터 생성 함수는 그대로 사용 (Redis에 삽입해야 RDB 생성 가능)
def generate_vehicles(n=200):
    vehicles_commands = []
    for i in range(1, n+1):
        data = {
            "id": str(i),
            "plate": f"{random.randint(10,99)}{random.choice(['가','나','다','라','마','바','사','아','자','차','카','타','파','하'])}{random.randint(1000,9999)}",
            "status": random.choice(["available", "in_use", "maintenance"]),
            "location": random.choice(["부산창고", "서울1창고", "서울2창고", "대전창고", "인천창고", "광주창고"]),
            "capacity": str(random.randint(500, 1500))
        }
        command_parts = [f"HMSET vehicle:{i}"]
        for key, value in data.items():
            command_parts.append(f"{key} \"{value}\"")
        vehicles_commands.append(" ".join(command_parts))
    return vehicles_commands

def generate_orders_and_recall(n=200):
    orders_commands = []
    recall_commands = []
    for i in range(1, n+1):
        order_id = f"ORD{1000+i}"
        status = random.choice(["requested", "scheduled", "in_transit", "completed"])
        data = {
            "order_id": order_id,
            "customer_name": random.choice(["김철수", "이영희", "박민수", "최지현", "정하늘", "윤지호"]),
            "address": random.choice(["서울","부산","대전","광주","인천","대구","울산"]) + "시 " + str(random.randint(1,20)) + "구 " + str(random.randint(1,300)) + "번지",
            "product_id": f"P{1000+random.randint(1,199)}",
            "status": status,
            "request_date": str(datetime.date.today())
        }
        if status == "completed":
            data["completed_at"] = str(datetime.date.today() - datetime.timedelta(days=random.randint(1, 5)))
        elif status in ["scheduled", "in_transit"]:
            data["delivery_date"] = str(datetime.date.today() + datetime.timedelta(days=random.randint(1, 7)))
        
        order_command_parts = [f"HMSET delivery:order:{order_id}"]
        for key, value in data.items():
            order_command_parts.append(f"{key} \"{value}\"")
        orders_commands.append(" ".join(order_command_parts))

        if random.random() < 0.3:
            data["recall_reason"] = random.choice(["안전 문제", "품질 불량", "제조사 요청"])
            data["pickup_date"] = str(datetime.date.today() + datetime.timedelta(days=random.randint(1, 5)))
            
            recall_command_parts = [f"HMSET delivery:recall:{order_id}"]
            for key, value in data.items():
                recall_command_parts.append(f"{key} \"{value}\"")
            recall_commands.append(" ".join(recall_command_parts))
    
    return orders_commands, recall_commands

def generate_inventory(n=200):
    inventory_commands = []
    for i in range(1, n+1):
        data = {
            "product_id": f"P{1000+random.randint(1,199)}",
            "warehouse": random.choice(["A","B","C","D"]),
            "type": "recall",
            "quantity": str(random.randint(10, 500))
        }
        command_parts = [f"HMSET item:warehouse:{data['warehouse']}:{data['product_id']}:{i}"]
        for key, value in data.items():
            command_parts.append(f"{key} \"{value}\"")
        inventory_commands.append(" ".join(command_parts))
    return inventory_commands

def generate_quality(n=200):
    quality_commands = []
    for i in range(1, n+1):
        order_id = f"ORDQC{2000+i}"
        qc_result = random.choice(["sellable","defect","quarantine"])
        data = {
            "order_id": order_id,
            "product_id": f"P{1000+random.randint(1,199)}",
            "qc_result": qc_result,
            "checked_at": str(datetime.date.today())
        }
        if qc_result == "defect":
            data["disposition"] = random.choice(["discard","repack","repair"])
            data["defect_code"] = f"D{random.randint(1,5)}"
        
        command_parts = [f"HMSET quality:return:{order_id}"]
        for key, value in data.items():
            command_parts.append(f"{key} \"{value}\"")
        quality_commands.append(" ".join(command_parts))
    return quality_commands

if __name__ == "__main__":
    # 데이터 삽입
    all_commands = []
    all_commands.extend(generate_vehicles(200))
    orders_commands, recall_commands = generate_orders_and_recall(200)
    all_commands.extend(orders_commands)
    all_commands.extend(recall_commands)
    all_commands.extend(generate_inventory(200))
    all_commands.extend(generate_quality(200))

    with open("all_data_commands.txt", "w", encoding="utf-8") as f:
        for command in all_commands:
            f.write(command + "\n")

    print("✅ 예시 데이터 HMSET 명령 TXT 파일 생성 완료: all_data_commands.txt")
    