"""
OKX Cross-Chain Bridge API Backend
通用的跨链桥后端服务，基于OKX DEX API
可复用于其他项目
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
from typing import Dict, Any, List, Optional
import uvicorn

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 优先加载.env.local，然后加载.env
    load_dotenv('.env.local')  # 本地配置优先
    load_dotenv('.env')        # 默认配置
    print("✅ 环境变量加载成功")
except ImportError:
    print("⚠️  python-dotenv未安装，跳过.env文件加载")

# 添加项目根目录到Python路径，以便导入OKX SDK
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from okx_crosschain_sdk import (
        Config,
        AssetExplorer,
        Quoter,
        TransactionBuilder,
        StatusTracker,
        OnChainGateway,
        APIError
    )
except ImportError as e:
    print(f"警告: 无法导入OKX SDK: {e}")
    print("请确保okx_crosschain_sdk目录在项目根目录下")

# 创建FastAPI应用
app = FastAPI(
    title="OKX Cross-Chain Bridge API",
    description="基于OKX DEX API的通用跨链桥后端服务",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# 配置CORS - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置和SDK实例
config = Config()  # 使用默认配置，不需要API Key的功能
asset_explorer = AssetExplorer(config)
quoter = Quoter(config)
transaction_builder = TransactionBuilder(config)
status_tracker = StatusTracker(config)

# 如果有API Key配置，可以初始化OnChainGateway
onchain_gateway = None
try:
    # 从环境变量读取API Key（可选）
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_SECRET_KEY")
    passphrase = os.getenv("OKX_PASSPHRASE")
    
    if api_key and secret_key and passphrase:
        auth_config = Config(api_key=api_key, secret_key=secret_key, passphrase=passphrase)
        onchain_gateway = OnChainGateway(auth_config)
        print("✅ OnChainGateway 初始化成功 (API Key已配置)")
    else:
        print("ℹ️  OnChainGateway 未初始化 (未配置API Key)")
except Exception as e:
    print(f"⚠️  OnChainGateway 初始化失败: {e}")

# 错误处理
@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=400,
        content={"error": "API调用失败", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误", "detail": str(exc)}
    )

# 根路径 - 健康检查
@app.get("/")
async def root():
    return {
        "message": "OKX Cross-Chain Bridge API",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "asset_explorer": True,
            "quoter": True,
            "transaction_builder": True,
            "status_tracker": True,
            "onchain_gateway": onchain_gateway is not None
        }
    }

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# 导入路由模块
from routers import chains, tokens, quote, transaction, status

# 注册路由
app.include_router(chains.router, prefix="/api/v1/chains", tags=["链信息"])
app.include_router(tokens.router, prefix="/api/v1/tokens", tags=["代币信息"])
app.include_router(quote.router, prefix="/api/v1/quote", tags=["询价"])
app.include_router(transaction.router, prefix="/api/v1/transaction", tags=["交易"])
app.include_router(status.router, prefix="/api/v1/status", tags=["状态查询"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3001,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    ) 