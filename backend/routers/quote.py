"""
询价相关API路由 - 跨链桥核心功能
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import sys
import os

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    load_dotenv('.env')
except ImportError:
    pass

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from okx_crosschain_sdk import Quoter, Config, APIError
    print("✅ 询价模块: OKX SDK 导入成功")
except ImportError as e:
    print(f"❌ 询价模块: OKX SDK 导入失败: {e}")
    Quoter = None
    Config = None
    APIError = Exception

router = APIRouter()

# 常见桥的Logo映射
BRIDGE_LOGOS = {
    "stargate": "https://stargate.finance/favicon.ico",
    "layerzero": "https://layerzero.network/favicon.ico", 
    "cbridge": "https://cbridge.celer.network/favicon.ico",
    "multichain": "https://multichain.org/favicon.ico",
    "hop": "https://hop.exchange/favicon.ico",
    "across": "https://across.to/favicon.ico",
    "synapse": "https://synapseprotocol.com/favicon.ico",
    "bridgers": "https://www.bridgers.xyz/favicon.ico",
    "butterswap": "https://www.butterswap.io/favicon.ico",
    "metapath": "https://metapath.org/favicon.ico",
    "default": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiMwMDdCRkYiLz4KPHN2ZyB4PSI4IiB5PSI4IiB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSI+CjxwYXRoIGQ9Ik04IDJMMTQgOEw4IDE0TDIgOEw4IDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4KPC9zdmc+"
}

# 请求模型
class QuoteRequest(BaseModel):
    from_chain_id: str = Field(..., description="源链ID")
    to_chain_id: str = Field(..., description="目标链ID")
    from_token_address: str = Field(..., description="源代币地址")
    to_token_address: str = Field(..., description="目标代币地址")
    amount: str = Field(..., description="交易数量")
    user_address: str = Field(..., description="用户钱包地址")
    slippage: Optional[str] = Field("0.5", description="滑点容忍度 (百分比)")
    preference: Optional[str] = Field("price", description="偏好: price(价格优先) 或 speed(速度优先)")
    gas_price: Optional[str] = Field(None, description="自定义Gas价格")
    sort_type: Optional[str] = Field("optimal", description="排序类型: optimal(最优), fastest(最快), most_tokens(数量最多)")

# 响应模型
class QuoteResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    message: str = ""

# 依赖注入：获取Quoter实例
def get_quoter():
    if Quoter is None:
        raise HTTPException(status_code=500, detail="OKX SDK未正确导入")
    
    # 从环境变量获取API Key配置
    api_key = os.getenv('OKX_API_KEY')
    secret_key = os.getenv('OKX_SECRET_KEY')
    passphrase = os.getenv('OKX_PASSPHRASE')
    
    # 如果有API Key配置，则使用认证配置，否则使用默认配置
    if api_key and secret_key and passphrase:
        print("✅ 使用API Key认证配置")
        config = Config(
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase
        )
    else:
        print("⚠️ 使用默认配置（无API Key认证）")
        config = Config()
    
    return Quoter(config)

@router.post("/", summary="获取跨链交易报价", response_model=QuoteResponse)
async def get_quote(
    request: QuoteRequest,
    quoter: Quoter = Depends(get_quoter)
) -> QuoteResponse:
    """
    获取跨链交易报价
    
    根据用户输入的交易参数，返回所有可用的跨链交易路径和报价信息。
    前端可以根据需要进行排序。
    """
    try:
        print(f"📝 收到报价请求:")
        print(f"  - 源链: {request.from_chain_id}")
        print(f"  - 目标链: {request.to_chain_id}")
        print(f"  - 源代币: {request.from_token_address}")
        print(f"  - 目标代币: {request.to_token_address}")
        print(f"  - 数量: {request.amount}")
        print(f"  - 用户地址: {request.user_address}")
        print(f"  - 滑点: {request.slippage}")
        
        # 获取所有路由 - 使用默认排序（最优路由）
        routes = quoter.get_quote(
            from_chain_id=request.from_chain_id,
            to_chain_id=request.to_chain_id,
            from_token_address=request.from_token_address,
            to_token_address=request.to_token_address,
            amount=request.amount,
            user_address=request.user_address,
            slippage=request.slippage,
            sort=1  # 使用最优路由获取更多选择
        )
        
        if not routes:
            return QuoteResponse(
                success=False,
                data=[],
                message="未找到可用的跨链路径，请检查参数或稍后重试"
            )
        
        print(f"🎯 获取到 {len(routes)} 条路径")
        
        # 增强路由信息，添加前端需要的字段
        enhanced_routes = []
        for i, route in enumerate(routes):
            # 从routerList中提取桥接信息
            router_list = route.get('routerList', [])
            bridge_name = "Unknown Bridge"
            bridge_id = "unknown"
            estimated_amount = "0"
            minimum_received = "0"
            total_fee_usd = "0.000"
            gas_fee_usd = "0.000"
            bridge_fee_usd = "0.000"
            bridge_logo_url = None
            
            if router_list and len(router_list) > 0:
                first_router = router_list[0]
                # 从router对象中获取桥信息
                router_info = first_router.get('router', {})
                bridge_name = router_info.get('bridgeName', 'Unknown Bridge')
                bridge_id = router_info.get('bridgeId', 'unknown')
                
                # 尝试获取桥logo（如果API返回了的话）
                bridge_logo_url = router_info.get('bridgeLogoUrl') or get_bridge_logo(bridge_name)
                
                # 获取金额信息
                estimated_amount = first_router.get('toTokenAmount', '0')
                minimum_received = first_router.get('minimumReceived', estimated_amount)
                
                # 计算费用 - 保留3位小数
                cross_chain_fee_usd = float(router_info.get('crossChainFeeUsd', '0'))
                estimate_gas_fee_usd = float(first_router.get('estimateGasFeeUsd', '0'))
                bridge_fee_usd = f"{cross_chain_fee_usd:.3f}"
                gas_fee_usd = f"{estimate_gas_fee_usd:.3f}"
                total_fee_usd = f"{cross_chain_fee_usd + estimate_gas_fee_usd:.3f}"
            
            # 从toToken中获取代币信息
            to_token = route.get('toToken', {})
            to_token_symbol = to_token.get('tokenSymbol', 'Unknown')
            to_token_decimals = to_token.get('decimals', '18')
            to_token_logo = to_token.get('tokenLogoUrl', '')
            
            # 从fromToken中获取代币信息
            from_token = route.get('fromToken', {})
            from_token_symbol = from_token.get('tokenSymbol', 'Unknown')
            from_token_logo = from_token.get('tokenLogoUrl', '')
            
            enhanced_route = {
                # 原始数据
                **route,
                # 映射到前端期望的字段
                "bridgeName": bridge_name,
                "bridgeId": bridge_id,
                "bridgeLogoUrl": bridge_logo_url,
                "toTokenAmount": estimated_amount,
                "estimatedAmount": estimated_amount,
                "minimumReceived": minimum_received,
                "totalFeeUsd": total_fee_usd,
                "gasFeeUsd": gas_fee_usd,
                "bridgeFeeUsd": bridge_fee_usd,
                "priceImpact": "0",  # OKX API可能不直接提供
                # 添加路由排名
                "rank": i + 1,
                "isRecommended": i == 0,  # 第一个为推荐路由
                # 添加预计时间信息
                "estimatedTime": estimate_transaction_time(route),
                # 添加安全评级
                "safetyRating": get_safety_rating(route),
                # 格式化费用信息
                "formattedFees": format_fee_info({
                    "totalFeeUsd": total_fee_usd,
                    "gasFeeUsd": gas_fee_usd,
                    "bridgeFeeUsd": bridge_fee_usd
                }),
                # 添加路由步骤详情 - 包含真实的代币logo
                "routeSteps": parse_route_steps({
                    **route,
                    "bridgeName": bridge_name,
                    "fromTokenSymbol": from_token_symbol,
                    "fromTokenLogo": from_token_logo,
                    "toTokenSymbol": to_token_symbol,
                    "toTokenLogo": to_token_logo,
                    "estimatedAmount": estimated_amount
                }),
                # 添加代币logo信息
                "fromTokenLogo": from_token_logo,
                "toTokenLogo": to_token_logo
            }
            enhanced_routes.append(enhanced_route)
        
        return QuoteResponse(
            success=True,
            data=enhanced_routes,
            message=f"成功获取到 {len(enhanced_routes)} 条路由报价"
        )
        
    except APIError as e:
        print(f"❌ API错误: {e}")
        raise HTTPException(status_code=400, detail=f"获取报价失败: {str(e)}")
    except ValueError as e:
        print(f"❌ 参数错误: {e}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# 辅助函数：获取桥logo
def get_bridge_logo(bridge_name: str) -> str | None:
    """根据桥名称获取logo URL，如果没有则返回None"""
    bridge_key = bridge_name.lower().replace(' ', '').replace('-', '')
    
    # 尝试匹配常见桥名
    for key, logo_url in BRIDGE_LOGOS.items():
        if key != "default" and (key in bridge_key or bridge_key in key):
            return logo_url
    
    # 如果没有匹配到，返回None，前端只显示名字
    return None

# 辅助函数：解析路由步骤 - 包含真实代币logo
def parse_route_steps(route: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析路由步骤，便于前端显示交易流程，包含真实的代币logo"""
    steps = []
    
    # 第一步：源链操作
    steps.append({
        "step": 1,
        "action": "发送",
        "chainId": route.get("fromChainId"),
        "token": route.get("fromTokenSymbol"),
        "tokenLogo": route.get("fromTokenLogo"),
        "amount": route.get("fromTokenAmount"),
        "description": f"在源链发送 {route.get('fromTokenAmount')} {route.get('fromTokenSymbol')}"
    })
    
    # 第二步：跨链桥接
    steps.append({
        "step": 2,
        "action": "桥接",
        "bridge": route.get("bridgeName"),
        "description": f"通过 {route.get('bridgeName')} 进行跨链桥接"
    })
    
    # 第三步：目标链接收
    steps.append({
        "step": 3,
        "action": "接收",
        "chainId": route.get("toChainId"),
        "token": route.get("toTokenSymbol"),
        "tokenLogo": route.get("toTokenLogo"),
        "amount": route.get("estimatedAmount"),
        "description": f"在目标链接收 {route.get('estimatedAmount')} {route.get('toTokenSymbol')}"
    })
    
    return steps

# 辅助函数：格式化费用信息 - 包含详细分解
def format_fee_info(fees: Dict[str, Any]) -> Dict[str, Any]:
    """格式化费用信息，便于前端显示详细分解"""
    total_fee_usd = fees.get("totalFeeUsd", "0.000")
    gas_fee_usd = fees.get("gasFeeUsd", "0.000")
    bridge_fee_usd = fees.get("bridgeFeeUsd", "0.000")
    
    return {
        "totalFeeUsd": total_fee_usd,
        "formattedFee": f"${total_fee_usd}",
        "breakdown": {
            "gasFee": {
                "amount": gas_fee_usd,
                "formatted": f"${gas_fee_usd}",
                "description": "网络Gas费用"
            },
            "bridgeFee": {
                "amount": bridge_fee_usd,
                "formatted": f"${bridge_fee_usd}",
                "description": "跨链桥手续费"
            }
        },
        "hasBreakdown": float(gas_fee_usd) > 0 or float(bridge_fee_usd) > 0
    }

@router.get("/estimate-time", summary="预估跨链交易时间")
async def estimate_time(
    from_chain_id: str,
    to_chain_id: str,
    bridge_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    预估跨链交易时间
    
    参数:
    - from_chain_id: 源链ID
    - to_chain_id: 目标链ID  
    - bridge_name: 桥名称 (可选)
    """
    try:
        # 基于链和桥的组合预估时间
        estimated_minutes = estimate_time_by_chains(from_chain_id, to_chain_id, bridge_name)
        
        return {
            "estimatedMinutes": estimated_minutes,
            "estimatedRange": f"{estimated_minutes-1}-{estimated_minutes+2}分钟",
            "factors": get_time_factors(from_chain_id, to_chain_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预估时间失败: {str(e)}")

@router.get("/supported-pairs", summary="获取支持的交易对")
async def get_supported_pairs(
    quoter: Quoter = Depends(get_quoter)
) -> Dict[str, Any]:
    """
    获取支持的跨链交易对
    
    返回所有支持的源链->目标链组合
    """
    try:
        # 这里可以调用SDK获取支持的链，然后组合出所有可能的交易对
        # 由于OKX API可能没有直接的接口，我们返回常见的组合
        
        common_pairs = [
            {"from": "1", "to": "56", "popular": True},    # ETH -> BSC
            {"from": "1", "to": "137", "popular": True},   # ETH -> Polygon
            {"from": "1", "to": "10", "popular": True},    # ETH -> Optimism
            {"from": "1", "to": "42161", "popular": True}, # ETH -> Arbitrum
            {"from": "56", "to": "1", "popular": True},    # BSC -> ETH
            {"from": "56", "to": "137", "popular": False}, # BSC -> Polygon
            {"from": "137", "to": "1", "popular": True},   # Polygon -> ETH
            {"from": "137", "to": "56", "popular": False}, # Polygon -> BSC
        ]
        
        return {
            "supportedPairs": common_pairs,
            "totalPairs": len(common_pairs),
            "note": "实际支持的交易对以询价结果为准"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易对失败: {str(e)}")

# 辅助函数：预估交易时间
def estimate_transaction_time(route: Dict[str, Any]) -> Dict[str, Any]:
    """根据路由信息预估交易时间"""
    bridge_name = route.get("bridgeName", "").lower()
    from_chain = route.get("fromChainId", "")
    to_chain = route.get("toChainId", "")
    
    # 基于桥和链的组合预估时间
    base_time = 5  # 基础时间5分钟
    
    # 不同桥的时间调整
    if "stargate" in bridge_name:
        base_time = 3
    elif "layerzero" in bridge_name:
        base_time = 4
    elif "multichain" in bridge_name:
        base_time = 8
    elif "cbridge" in bridge_name:
        base_time = 6
    
    # 不同链的时间调整
    if from_chain == "1" or to_chain == "1":  # 以太坊较慢
        base_time += 2
    if from_chain == "56" or to_chain == "56":  # BSC较快
        base_time -= 1
        
    return {
        "estimatedMinutes": max(base_time, 2),  # 最少2分钟
        "range": f"{max(base_time-1, 1)}-{base_time+3}分钟"
    }

# 辅助函数：获取安全评级
def get_safety_rating(route: Dict[str, Any]) -> Dict[str, Any]:
    """根据桥和路由信息评估安全等级"""
    bridge_name = route.get("bridgeName", "").lower()
    
    # 基于桥的声誉评级
    if bridge_name in ["stargate", "layerzero"]:
        rating = "A"
        score = 95
    elif bridge_name in ["cbridge", "multichain"]:
        rating = "B+"
        score = 85
    else:
        rating = "B"
        score = 80
        
    return {
        "rating": rating,
        "score": score,
        "factors": ["桥协议安全性", "TVL规模", "审计情况"]
    }

# 辅助函数：基于链预估时间
def estimate_time_by_chains(from_chain_id: str, to_chain_id: str, bridge_name: Optional[str] = None) -> int:
    """基于链组合预估交易时间"""
    # 链的基础确认时间 (分钟)
    chain_times = {
        "1": 3,    # Ethereum
        "56": 1,   # BSC
        "137": 1,  # Polygon
        "10": 1,   # Optimism
        "42161": 1 # Arbitrum
    }
    
    from_time = chain_times.get(from_chain_id, 2)
    to_time = chain_times.get(to_chain_id, 2)
    bridge_time = 2  # 桥接基础时间
    
    return from_time + bridge_time + to_time

# 辅助函数：获取影响时间的因素
def get_time_factors(from_chain_id: str, to_chain_id: str) -> List[str]:
    """获取影响交易时间的因素"""
    factors = ["网络拥堵情况", "桥协议处理速度"]
    
    if from_chain_id == "1":
        factors.append("以太坊网络确认时间")
    if to_chain_id == "1":
        factors.append("以太坊网络确认时间")
        
    return factors 