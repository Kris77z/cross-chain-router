#!/usr/bin/env python3
"""
OKX Cross-Chain Bridge API 启动脚本
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

def main():
    """启动FastAPI服务器"""
    
    # 检查OKX SDK是否可用
    try:
        from okx_crosschain_sdk import Config
        print("✅ OKX SDK 导入成功")
    except ImportError as e:
        print(f"⚠️  警告: OKX SDK 导入失败: {e}")
        print("请确保 okx_crosschain_sdk 目录在项目根目录下")
    
    # 服务器配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 3001))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"""
🚀 启动 OKX Cross-Chain Bridge API
📍 地址: http://{host}:{port}
📚 API文档: http://{host}:{port}/docs
🔄 ReDoc: http://{host}:{port}/redoc
🐛 调试模式: {debug}
    """)
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )

if __name__ == "__main__":
    main() 