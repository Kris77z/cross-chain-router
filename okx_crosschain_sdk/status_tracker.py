# okx_crosschain_sdk/status_tracker.py

from .http_client import make_request, APIError
from .config import Config, get_default_config
from typing import Dict, Any, Optional

class StatusTracker:
    """
    状态追踪器，用于查询跨链交易的执行状态
    """
    
    def __init__(self, config: Config = None):
        """
        初始化状态追踪器
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or get_default_config()
    
    def get_transaction_status(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """
        查询跨链交易状态
        
        Args:
            tx_id: OKX内部交易ID
            
        Returns:
            交易状态信息字典，如果查询失败返回None
            
        Raises:
            APIError: 当API调用失败时抛出
        """
        try:
            # OKX DEX API的交易状态查询端点
            endpoint = "/api/v5/dex/cross-chain/status"
            
            params = {
                "txId": tx_id
            }
            
            response = make_request(
                method="GET",
                endpoint=endpoint,
                config=self.config,
                params=params
            )
            
            # 检查响应数据
            if response and 'data' in response and response['data']:
                return response['data'][0] if isinstance(response['data'], list) else response['data']
            
            return None
            
        except APIError as e:
            # 重新抛出API错误，让调用方处理
            raise e
        except Exception as e:
            # 包装其他异常为APIError
            raise APIError(f"查询交易状态时发生未知错误: {str(e)}")
    
    def get_transaction_history(self, user_address: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        查询用户的跨链交易历史
        
        Args:
            user_address: 用户钱包地址
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            包含交易历史的字典
            
        Raises:
            APIError: 当API调用失败时抛出
        """
        try:
            # 注意：这个端点可能不存在于OKX API中，这里是示例实现
            endpoint = "/api/v5/dex/cross-chain/history"
            
            params = {
                "address": user_address,
                "limit": str(limit),
                "offset": str(offset)
            }
            
            response = make_request(
                method="GET",
                endpoint=endpoint,
                config=self.config,
                params=params
            )
            
            return response if response else {"data": [], "total": 0}
            
        except APIError as e:
            # 如果API不存在，返回空结果而不是抛出错误
            if e.status_code == 404:
                return {"data": [], "total": 0, "message": "历史查询功能暂不可用"}
            raise e
        except Exception as e:
            raise APIError(f"查询交易历史时发生未知错误: {str(e)}")
    
    def batch_get_transaction_status(self, tx_ids: list) -> Dict[str, Dict[str, Any]]:
        """
        批量查询多个交易的状态
        
        Args:
            tx_ids: 交易ID列表
            
        Returns:
            以交易ID为键，状态信息为值的字典
            
        Raises:
            APIError: 当API调用失败时抛出
        """
        results = {}
        
        # 由于OKX API可能不支持批量查询，我们逐个查询
        for tx_id in tx_ids:
            try:
                status = self.get_transaction_status(tx_id)
                results[tx_id] = status if status else {"error": "交易未找到"}
            except APIError as e:
                results[tx_id] = {"error": str(e)}
            except Exception as e:
                results[tx_id] = {"error": f"查询失败: {str(e)}"}
        
        return results 