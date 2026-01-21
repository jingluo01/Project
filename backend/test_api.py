#!/usr/bin/env python3
"""
API 接口测试脚本
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_health():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_register():
    """测试用户注册接口"""
    print("\n🔍 测试用户注册接口...")
    try:
        data = {
            "username": "test_user",
            "password": "123456",
            "user_no": "2021001234",
            "role": 1
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 注册测试失败: {e}")
        return False

def test_login():
    """测试用户登录接口"""
    print("\n🔍 测试用户登录接口...")
    try:
        # 使用用户名登录
        data = {
            "username": "test_user",
            "password": "123456"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        print(f"用户名登录 - 状态码: {response.status_code}")
        print(f"用户名登录 - 响应: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始 API 接口测试...")
    
    # 测试健康检查
    if not test_health():
        print("❌ 服务未启动，请先启动应用")
        exit(1)
    
    # 测试注册
    test_register()
    
    # 测试登录
    test_login()
    
    print("\n✅ API 测试完成！")