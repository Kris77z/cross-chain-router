"""
交易状态查询相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from okx_crosschain_sdk import StatusTracker, Config, APIError
except ImportError:
    StatusTracker = None
    Config = None
    APIError = Exception

router = APIRouter()

# 依赖注入：获取StatusTracker实例
def get_status_tracker():
    if StatusTracker is None:
        raise HTTPException(status_code=500, detail="OKX SDK未正确导入")
    return StatusTracker(Config())

@router.get("/{tx_id}", summary="查询交易状态")
async def get_transaction_status(
    tx_id: str,
    status_tracker: StatusTracker = Depends(get_status_tracker)
) -> Dict[str, Any]:
    """
    查询跨链交易的执行状态
    
    参数:
    - tx_id: OKX内部交易ID (从构建交易接口获得)
    """
    try:
        # 调用SDK查询交易状态
        status_info = status_tracker.get_transaction_status(tx_id=tx_id)
        
        if not status_info:
            raise HTTPException(status_code=404, detail=f"未找到交易ID为 {tx_id} 的交易")
        
        # 增强状态信息
        enhanced_status = {
            **status_info,
            "txId": tx_id,
            "statusDescription": get_status_description(status_info.get("state", "")),
            "progressPercentage": get_progress_percentage(status_info.get("state", "")),
            "nextSteps": get_next_steps(status_info.get("state", "")),
            "estimatedCompletion": get_estimated_completion(status_info),
            "explorerLinks": get_explorer_links(status_info)
        }
        
        return enhanced_status
        
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"查询交易状态失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/batch/{tx_ids}", summary="批量查询交易状态")
async def get_batch_transaction_status(
    tx_ids: str,  # 逗号分隔的交易ID列表
    status_tracker: StatusTracker = Depends(get_status_tracker)
) -> List[Dict[str, Any]]:
    """
    批量查询多个交易的状态
    
    参数:
    - tx_ids: 逗号分隔的交易ID列表 (如: "tx1,tx2,tx3")
    """
    try:
        tx_id_list = [tx_id.strip() for tx_id in tx_ids.split(",")]
        
        if len(tx_id_list) > 10:
            raise HTTPException(status_code=400, detail="一次最多查询10个交易")
        
        results = []
        for tx_id in tx_id_list:
            try:
                status_info = status_tracker.get_transaction_status(tx_id=tx_id)
                if status_info:
                    enhanced_status = {
                        **status_info,
                        "txId": tx_id,
                        "statusDescription": get_status_description(status_info.get("state", "")),
                        "progressPercentage": get_progress_percentage(status_info.get("state", ""))
                    }
                    results.append(enhanced_status)
                else:
                    results.append({
                        "txId": tx_id,
                        "state": "not_found",
                        "statusDescription": "交易未找到",
                        "progressPercentage": 0
                    })
            except Exception as e:
                results.append({
                    "txId": tx_id,
                    "state": "error",
                    "statusDescription": f"查询失败: {str(e)}",
                    "progressPercentage": 0
                })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")

@router.get("/history/{user_address}", summary="查询用户交易历史")
async def get_user_transaction_history(
    user_address: str,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    查询用户的跨链交易历史
    
    注意: 这个功能需要后端维护用户交易记录，
    或者调用OKX提供的历史查询接口 (如果有的话)
    
    参数:
    - user_address: 用户钱包地址
    - limit: 返回数量限制
    - offset: 偏移量
    """
    try:
        # 这里应该从数据库或OKX API查询用户历史
        # 目前返回模拟数据
        mock_history = get_mock_transaction_history(user_address, limit, offset)
        
        return {
            "userAddress": user_address,
            "transactions": mock_history,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(mock_history),
                "hasMore": False
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询历史失败: {str(e)}")

# 辅助函数：获取状态描述
def get_status_description(state: str) -> str:
    """根据状态码返回中文描述"""
    status_descriptions = {
        "pending": "交易待处理",
        "processing": "交易处理中",
        "bridging": "跨链桥接中",
        "confirming": "等待确认",
        "completed": "交易完成",
        "failed": "交易失败",
        "cancelled": "交易取消",
        "timeout": "交易超时"
    }
    return status_descriptions.get(state.lower(), f"未知状态: {state}")

# 辅助函数：获取进度百分比
def get_progress_percentage(state: str) -> int:
    """根据状态返回进度百分比"""
    progress_mapping = {
        "pending": 10,
        "processing": 30,
        "bridging": 60,
        "confirming": 80,
        "completed": 100,
        "failed": 0,
        "cancelled": 0,
        "timeout": 0
    }
    return progress_mapping.get(state.lower(), 0)

# 辅助函数：获取下一步操作
def get_next_steps(state: str) -> List[str]:
    """根据状态返回用户可能需要的下一步操作"""
    next_steps_mapping = {
        "pending": ["等待交易被矿工打包", "可以通过区块浏览器查看交易状态"],
        "processing": ["交易正在源链处理", "请耐心等待"],
        "bridging": ["跨链桥正在处理", "通常需要几分钟时间"],
        "confirming": ["等待目标链确认", "即将完成"],
        "completed": ["交易已完成", "可以在目标链查看余额"],
        "failed": ["交易失败", "请检查失败原因", "可能需要重新发起交易"],
        "cancelled": ["交易已取消", "如需继续请重新发起"],
        "timeout": ["交易超时", "请联系客服或重新发起交易"]
    }
    return next_steps_mapping.get(state.lower(), ["请联系客服获取帮助"])

# 辅助函数：预估完成时间
def get_estimated_completion(status_info: Dict[str, Any]) -> str:
    """根据当前状态预估完成时间"""
    state = status_info.get("state", "").lower()
    
    if state == "completed":
        return "已完成"
    elif state in ["failed", "cancelled", "timeout"]:
        return "不适用"
    elif state == "confirming":
        return "1-2分钟内"
    elif state == "bridging":
        return "2-5分钟内"
    elif state in ["pending", "processing"]:
        return "5-10分钟内"
    else:
        return "未知"

# 辅助函数：获取区块浏览器链接
def get_explorer_links(status_info: Dict[str, Any]) -> Dict[str, str]:
    """生成区块浏览器链接"""
    links = {}
    
    # 源链交易链接
    from_tx_hash = status_info.get("fromTxHash")
    from_chain_id = status_info.get("fromChainId")
    if from_tx_hash and from_chain_id:
        links["sourceTransaction"] = get_explorer_url(from_chain_id, from_tx_hash)
    
    # 目标链交易链接
    to_tx_hash = status_info.get("toTxHash")
    to_chain_id = status_info.get("toChainId")
    if to_tx_hash and to_chain_id:
        links["destinationTransaction"] = get_explorer_url(to_chain_id, to_tx_hash)
    
    return links

# 辅助函数：获取区块浏览器URL
def get_explorer_url(chain_id: str, tx_hash: str) -> str:
    """根据链ID和交易哈希生成区块浏览器URL"""
    explorer_base_urls = {
        "1": "https://etherscan.io/tx/",
        "56": "https://bscscan.com/tx/",
        "137": "https://polygonscan.com/tx/",
        "10": "https://optimistic.etherscan.io/tx/",
        "42161": "https://arbiscan.io/tx/",
        "43114": "https://snowtrace.io/tx/",
        "250": "https://ftmscan.com/tx/"
    }
    
    base_url = explorer_base_urls.get(chain_id, "")
    if base_url:
        return f"{base_url}{tx_hash}"
    return ""

# 辅助函数：获取模拟交易历史
def get_mock_transaction_history(user_address: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """返回模拟的交易历史数据"""
    # 在实际应用中，这里应该从数据库查询真实的历史记录
    mock_transactions = [
        {
            "txId": "mock_tx_1",
            "fromChainId": "1",
            "toChainId": "56",
            "fromTokenSymbol": "USDC",
            "toTokenSymbol": "USDC",
            "fromTokenAmount": "100.0",
            "estimatedAmount": "99.5",
            "state": "completed",
            "bridgeName": "Stargate",
            "timestamp": "2024-01-15T10:30:00Z",
            "fromTxHash": "0x123...",
            "toTxHash": "0x456..."
        },
        {
            "txId": "mock_tx_2",
            "fromChainId": "56",
            "toChainId": "137",
            "fromTokenSymbol": "BNB",
            "toTokenSymbol": "MATIC",
            "fromTokenAmount": "1.0",
            "estimatedAmount": "150.0",
            "state": "processing",
            "bridgeName": "Multichain",
            "timestamp": "2024-01-15T09:15:00Z",
            "fromTxHash": "0x789...",
            "toTxHash": null
        }
    ]
    
    # 应用分页
    start = offset
    end = offset + limit
    return mock_transactions[start:end] 