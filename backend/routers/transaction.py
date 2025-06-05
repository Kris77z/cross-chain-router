"""
交易构建相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from okx_crosschain_sdk import TransactionBuilder, Config, APIError
except ImportError:
    TransactionBuilder = None
    Config = None
    APIError = Exception

router = APIRouter()

# 请求模型
class ApproveRequest(BaseModel):
    route_data: Dict[str, Any] = Field(..., description="询价返回的路由数据")

class BuildTransactionRequest(BaseModel):
    route_data: Dict[str, Any] = Field(..., description="询价返回的路由数据")
    approve_tx_id: Optional[str] = Field(None, description="授权交易哈希")
    gas_price: Optional[str] = Field(None, description="自定义Gas价格")

# 依赖注入：获取TransactionBuilder实例
def get_transaction_builder():
    if TransactionBuilder is None:
        raise HTTPException(status_code=500, detail="OKX SDK未正确导入")
    return TransactionBuilder(Config())

@router.post("/approve", summary="获取ERC20授权交易数据")
async def get_approve_transaction(
    request: ApproveRequest,
    tx_builder: TransactionBuilder = Depends(get_transaction_builder)
) -> Dict[str, Any]:
    """
    获取ERC20代币授权交易的数据
    
    在执行跨链交易前，通常需要先授权代币给路由合约
    """
    try:
        # 调用SDK获取授权交易数据
        approve_data = tx_builder.get_approve_transaction_data(
            route_data=request.route_data
        )
        
        if not approve_data:
            raise HTTPException(status_code=400, detail="无法生成授权交易数据")
        
        # 增强授权数据，添加前端需要的信息
        enhanced_approve_data = {
            **approve_data,
            "transactionType": "approve",
            "description": "授权代币给路由合约",
            "estimatedGas": approve_data.get("gasLimit", "60000"),
            "tokenInfo": {
                "symbol": request.route_data.get("fromTokenSymbol", ""),
                "address": request.route_data.get("fromTokenAddress", ""),
                "amount": request.route_data.get("fromTokenAmount", "")
            }
        }
        
        return enhanced_approve_data
        
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"获取授权交易数据失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.post("/build", summary="构建跨链交易数据")
async def build_transaction(
    request: BuildTransactionRequest,
    tx_builder: TransactionBuilder = Depends(get_transaction_builder)
) -> Dict[str, Any]:
    """
    构建实际的跨链交易数据
    
    基于询价结果构建可以发送到区块链的交易数据
    """
    try:
        # 调用SDK构建交易数据
        build_params = {
            "route_data": request.route_data
        }
        
        # 添加可选参数
        if request.approve_tx_id:
            build_params["approve_tx_id"] = request.approve_tx_id
        if request.gas_price:
            build_params["gas_price"] = request.gas_price
        
        tx_data = tx_builder.get_build_transaction_data(**build_params)
        
        if not tx_data:
            raise HTTPException(status_code=400, detail="无法构建交易数据")
        
        # 增强交易数据
        enhanced_tx_data = {
            **tx_data,
            "transactionType": "crosschain",
            "description": "跨链交易",
            "routeInfo": {
                "fromChain": request.route_data.get("fromChainId", ""),
                "toChain": request.route_data.get("toChainId", ""),
                "fromToken": request.route_data.get("fromTokenSymbol", ""),
                "toToken": request.route_data.get("toTokenSymbol", ""),
                "bridge": request.route_data.get("bridgeName", "")
            },
            "estimatedReceive": {
                "amount": request.route_data.get("estimatedAmount", ""),
                "symbol": request.route_data.get("toTokenSymbol", "")
            }
        }
        
        return enhanced_tx_data
        
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"构建交易数据失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/gas-estimate", summary="预估交易Gas费用")
async def estimate_gas_fee(
    chain_id: str,
    transaction_type: str = "crosschain"  # approve 或 crosschain
) -> Dict[str, Any]:
    """
    预估交易的Gas费用
    
    参数:
    - chain_id: 链ID
    - transaction_type: 交易类型 (approve 或 crosschain)
    """
    try:
        # 基于链和交易类型预估Gas
        gas_estimates = get_gas_estimates(chain_id, transaction_type)
        
        return {
            "chainId": chain_id,
            "transactionType": transaction_type,
            "gasEstimates": gas_estimates,
            "recommendations": get_gas_recommendations(chain_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预估Gas费用失败: {str(e)}")

# 辅助函数：获取Gas预估
def get_gas_estimates(chain_id: str, transaction_type: str) -> Dict[str, Any]:
    """根据链和交易类型预估Gas"""
    
    # 不同链的基础Gas价格 (Gwei)
    base_gas_prices = {
        "1": {"slow": 20, "standard": 25, "fast": 35},      # Ethereum
        "56": {"slow": 3, "standard": 5, "fast": 8},        # BSC
        "137": {"slow": 30, "standard": 35, "fast": 50},    # Polygon
        "10": {"slow": 0.001, "standard": 0.001, "fast": 0.002},  # Optimism
        "42161": {"slow": 0.1, "standard": 0.1, "fast": 0.2}      # Arbitrum
    }
    
    # 不同交易类型的Gas Limit
    gas_limits = {
        "approve": 60000,
        "crosschain": 200000
    }
    
    gas_price = base_gas_prices.get(chain_id, {"slow": 10, "standard": 15, "fast": 25})
    gas_limit = gas_limits.get(transaction_type, 150000)
    
    # 计算费用 (ETH)
    estimates = {}
    for speed, price in gas_price.items():
        gas_fee_eth = (price * gas_limit) / 1e9  # 转换为ETH
        gas_fee_usd = gas_fee_eth * 2000  # 假设ETH价格为2000 USD
        
        estimates[speed] = {
            "gasPrice": f"{price}",
            "gasLimit": str(gas_limit),
            "gasFeeEth": f"{gas_fee_eth:.6f}",
            "gasFeeUsd": f"{gas_fee_usd:.2f}"
        }
    
    return estimates

# 辅助函数：获取Gas建议
def get_gas_recommendations(chain_id: str) -> Dict[str, str]:
    """根据链提供Gas使用建议"""
    recommendations = {
        "1": "以太坊网络拥堵时建议使用Fast模式确保交易及时确认",
        "56": "BSC网络通常较快，Standard模式即可",
        "137": "Polygon网络建议使用Standard或Fast模式",
        "10": "Optimism网络Gas费用较低，建议使用Standard模式",
        "42161": "Arbitrum网络Gas费用较低，建议使用Standard模式"
    }
    
    return {
        "general": recommendations.get(chain_id, "建议根据网络拥堵情况选择合适的Gas价格"),
        "timing": "非紧急交易可选择Slow模式节省费用",
        "monitoring": "可通过区块浏览器监控交易状态"
    } 