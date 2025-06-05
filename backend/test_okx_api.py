#!/usr/bin/env python3
"""
测试OKX API的简单脚本
"""
import requests
import json
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env.local')

# 获取API Key
api_key = os.getenv('OKX_API_KEY')
secret_key = os.getenv('OKX_SECRET_KEY')
passphrase = os.getenv('OKX_PASSPHRASE')

print(f"API Key: {api_key[:10]}..." if api_key else "API Key: None")
print(f"Secret Key: {secret_key[:10]}..." if secret_key else "Secret Key: None")
print(f"Passphrase: {passphrase[:5]}..." if passphrase else "Passphrase: None")

# 测试1: 不带认证的请求
print("\n=== 测试1: 不带认证的请求 ===")
try:
    response = requests.get("https://web3.okx.com/api/v5/dex/cross-chain/supported/chain")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:200]}...")
except Exception as e:
    print(f"错误: {e}")

# 测试2: 带认证的请求
print("\n=== 测试2: 带认证的请求 ===")
if api_key and secret_key and passphrase:
    import hmac
    import hashlib
    import base64
    from datetime import datetime
    
    # 构建认证头
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    method = 'GET'
    request_path = '/api/v5/dex/cross-chain/supported/chain'
    body = ''
    
    # 生成签名
    prehash_str = timestamp + method + request_path + body
    mac = hmac.new(secret_key.encode('utf-8'), prehash_str.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(mac.digest()).decode('utf-8')
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get("https://web3.okx.com/api/v5/dex/cross-chain/supported/chain", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}...")
    except Exception as e:
        print(f"错误: {e}")
else:
    print("API Key信息不完整，跳过认证测试")

# 测试3: 测试一个已知的公开API
print("\n=== 测试3: 测试公开API ===")
try:
    response = requests.get("https://www.okx.com/api/v5/public/time")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}") 