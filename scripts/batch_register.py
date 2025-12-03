#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LQZC 商城压测用户批量注册脚本 v3.0

修复：
- 添加重试机制（失败自动重试3次）
- 降低并发避免服务器压力过大
- 确保所有用户都能成功注册并获取token
"""

import requests
import json
import csv
import time
import sys
from datetime import datetime

# ============== 配置区域 ==============
BASE_URL = "http://localhost:8001"
REGISTER_URL = f"{BASE_URL}/mall/customer/register"
LOGIN_URL = f"{BASE_URL}/mall/customer/login"

# 用户配置
PHONE_PREFIX = "138"           # 手机号前缀
START_NUMBER = 10000001        # 起始号码（不含前缀）
USER_COUNT = 12000             # 注册用户数量
DEFAULT_PASSWORD = "test123456"  # 统一测试密码
REGISTER_CHANNEL = "H5"        # 注册渠道

# 请求配置
MAX_RETRIES = 3                # 最大重试次数
REQUEST_TIMEOUT = 15           # 请求超时时间（秒）
REQUEST_DELAY = 0.05           # 每个请求间隔（秒）

# 输出文件
CSV_OUTPUT = "test_users.csv"
JSON_OUTPUT = "register_result.json"
# =====================================


def generate_phone(index):
    """生成手机号"""
    number = START_NUMBER + index
    return f"{PHONE_PREFIX}{number}"


def generate_nickname(phone):
    """生成昵称"""
    return f"测试用户{phone[-4:]}"


def register_user(phone, nickname, password, retries=MAX_RETRIES):
    """注册单个用户（带重试）"""
    payload = {
        "phone": phone,
        "nickname": nickname,
        "password": password,
        "registerChannel": REGISTER_CHANNEL
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(
                REGISTER_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT
            )
            result = response.json()
            is_success = result.get("code") == 200
            message = result.get("message", "")
            already_exists = "已注册" in message or "已存在" in message
            
            return {
                "success": is_success or already_exists,
                "message": message,
                "is_new": is_success and not already_exists,
                "already_exists": already_exists
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5)  # 重试前等待
                continue
            return {
                "success": False,
                "message": str(e),
                "is_new": False,
                "already_exists": False
            }


def login_user(phone, password, retries=MAX_RETRIES):
    """用户登录获取token（带重试）"""
    payload = {
        "phone": phone,
        "password": password
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(
                LOGIN_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT
            )
            result = response.json()
            if result.get("code") == 200 and result.get("data"):
                data = result["data"]
                return {
                    "success": True,
                    "token": data.get("token"),
                    "customer_id": data.get("customer", {}).get("id")
                }
            return {
                "success": False,
                "token": None,
                "customer_id": None,
                "message": result.get("message", "登录失败")
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
            return {
                "success": False,
                "token": None,
                "customer_id": None,
                "message": str(e)
            }


def process_user(index):
    """处理单个用户的注册和登录"""
    phone = generate_phone(index)
    nickname = generate_nickname(phone)
    
    result = {
        "index": index,
        "phone": phone,
        "nickname": nickname,
        "register_success": False,
        "is_new_user": False,
        "login_success": False,
        "token": None,
        "customer_id": None,
        "message": ""
    }
    
    # 1. 尝试注册
    reg_result = register_user(phone, nickname, DEFAULT_PASSWORD)
    
    if reg_result["success"]:
        result["register_success"] = True
        if reg_result["is_new"]:
            result["is_new_user"] = True
            result["message"] = "新注册"
        else:
            result["message"] = "已存在"
    else:
        result["message"] = f"注册失败: {reg_result['message']}"
    
    time.sleep(REQUEST_DELAY)
    
    # 2. 登录获取token
    login_result = login_user(phone, DEFAULT_PASSWORD)
    
    if login_result["success"]:
        result["login_success"] = True
        result["token"] = login_result["token"]
        result["customer_id"] = login_result["customer_id"]
        result["register_success"] = True
    else:
        result["message"] += f" | 登录失败: {login_result.get('message', '')}"
    
    return result


def main():
    """主函数 - 顺序执行，确保稳定"""
    print()
    print("=" * 70)
    print("LQZC 商城压测用户批量注册工具 v3.0 (稳定版)")
    print("=" * 70)
    print(f"目标服务器: {BASE_URL}")
    print(f"用户数量: {USER_COUNT}")
    print(f"手机号范围: {generate_phone(0)} - {generate_phone(USER_COUNT - 1)}")
    print(f"默认密码: {DEFAULT_PASSWORD}")
    print(f"重试次数: {MAX_RETRIES}")
    print("=" * 70)
    
    # 检查服务器连接
    print("\n检查服务器连接...")
    try:
        response = requests.get(f"{BASE_URL}/mall/coupon/market", timeout=5)
        print(f"✅ 服务器连接正常 (响应码: {response.status_code})")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(1)
    
    print()
    confirm = input(f"确认注册/登录 {USER_COUNT} 个用户? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        sys.exit(0)
    
    print()
    
    # 顺序处理每个用户
    results = []
    success_count = 0
    new_count = 0
    exists_count = 0
    fail_count = 0
    
    start_time = time.time()
    
    for i in range(USER_COUNT):
        result = process_user(i)
        results.append(result)
        
        if result["login_success"]:
            success_count += 1
            if result["is_new_user"]:
                new_count += 1
            else:
                exists_count += 1
        else:
            fail_count += 1
        
        # 进度显示
        if (i + 1) % 100 == 0 or (i + 1) == USER_COUNT:
            percent = ((i + 1) / USER_COUNT) * 100
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (USER_COUNT - i - 1) / rate if rate > 0 else 0
            print(f"\r进度: [{i+1}/{USER_COUNT}] {percent:.1f}% | "
                  f"成功: {success_count} (新:{new_count} 存在:{exists_count}) | "
                  f"失败: {fail_count} | "
                  f"速度: {rate:.1f}/s | ETA: {eta:.0f}s", end="", flush=True)
    
    elapsed_time = time.time() - start_time
    print(f"\n\n✅ 完成! 耗时: {elapsed_time:.1f}秒")
    
    # 按手机号排序
    results.sort(key=lambda x: x['phone'])
    
    # 导出CSV
    successful_users = [r for r in results if r["login_success"] and r["token"]]
    
    print(f"\n导出CSV: {CSV_OUTPUT}")
    with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['phone', 'token', 'customer_id'])
        for user in successful_users:
            writer.writerow([user['phone'], user['token'], user['customer_id']])
    print(f"  ✅ 导出 {len(successful_users)} 条用户数据")
    
    # 导出JSON
    print(f"导出JSON: {JSON_OUTPUT}")
    export_data = {
        "export_time": datetime.now().isoformat(),
        "summary": {
            "total": USER_COUNT,
            "success": success_count,
            "new": new_count,
            "exists": exists_count,
            "failed": fail_count
        },
        "users": results
    }
    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    # 汇总
    print()
    print("=" * 70)
    print("汇总")
    print("=" * 70)
    print(f"总计: {USER_COUNT}")
    print(f"成功: {success_count} (新注册: {new_count}, 已存在: {exists_count})")
    print(f"失败: {fail_count}")
    print(f"可用于JMeter: {len(successful_users)}")
    print()
    
    if len(successful_users) >= 10000:
        print("✅ 用户数量足够进行10000+并发测试！")
    elif len(successful_users) >= 1000:
        print("✅ 用户数量足够进行1000+并发测试！")


if __name__ == "__main__":
    main()
