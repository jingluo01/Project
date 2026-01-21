#!/usr/bin/env python3
"""
用户 API 接口测试脚本
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_login_and_get_token():
    """登录并获取token"""
    print("🔍 登录获取token...")
    try:
        data = {
            "username": "test_user",
            "password": "123456"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        if response.status_code == 200:
            result = response.json()
            token = result['data']['token']
            print(f"✅ 登录成功，获取到token")
            return token
        else:
            print(f"❌ 登录失败: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return None

def test_get_user_info(token):
    """测试获取用户信息接口"""
    print("\n🔍 测试获取用户信息接口...")
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{BASE_URL}/api/user/info", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 获取用户信息失败: {e}")
        return False

def test_bind_car(token):
    """测试绑定车辆接口"""
    print("\n🔍 测试绑定车辆接口...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "plate_number": "京A88888"
        }
        response = requests.post(f"{BASE_URL}/api/user/car", json=data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 绑定车辆失败: {e}")
        return False

def test_bind_duplicate_car(token):
    """测试绑定重复车辆"""
    print("\n🔍 测试绑定重复车辆...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "plate_number": "京A88888"  # 相同车牌
        }
        response = requests.post(f"{BASE_URL}/api/user/car", json=data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        # 应该返回错误
        return response.status_code != 200
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始用户 API 接口测试...")
    
    # 1. 登录获取token
    token = test_login_and_get_token()
    if not token:
        print("❌ 无法获取token，测试终止")
        exit(1)
    
    # 2. 测试获取用户信息
    test_get_user_info(token)
    
    # 3. 测试绑定车辆
    test_bind_car(token)
    
    # 4. 测试绑定重复车辆
    test_bind_duplicate_car(token)
    
    # 5. 再次获取用户信息，查看车辆列表
    print("\n🔍 再次获取用户信息，查看车辆列表...")
    test_get_user_info(token)
    
    print("\n✅ 用户 API 测试完成！")