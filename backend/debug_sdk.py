#!/usr/bin/env python3
"""
调试SDK实现
"""
import sys
import os
sys.path.append('..')

from dotenv import load_dotenv
load_dotenv('.env.local')

from okx_crosschain_sdk import AssetExplorer, Config, APIError

# 创建配置
api_key = os.getenv('OKX_API_KEY')
secret_key = os.getenv('OKX_SECRET_KEY')
passphrase = os.getenv('OKX_PASSPHRASE')

print(f"API Key: {api_key[:10]}..." if api_key else "API Key: None")

config = Config(
    api_key=api_key,
    secret_key=secret_key,
    passphrase=passphrase
)

print(f"Config API Key: {config.API_KEY[:10]}..." if config.API_KEY else "Config API Key: None")

# 创建AssetExplorer
explorer = AssetExplorer(config)

# 测试获取支持的链
print("\n=== 测试SDK获取支持的链 ===")
try:
    chains = explorer.get_supported_chains()
    print(f"成功获取到 {len(chains)} 条链信息")
    if chains:
        print(f"第一条链: {chains[0]}")
except APIError as e:
    print(f"SDK错误: {e}")
    print(f"状态码: {e.status_code}")
    print(f"响应数据: {e.response_data}")
except Exception as e:
    print(f"其他错误: {e}") 