from typing import Optional, Dict, Any, List
from .config import Config, get_default_config
from .http_client import make_request, APIError

class OnChainGateway:
    """
    封装 OKX 交易上链 (On-Chain Gateway / Pre-transaction) API。
    提供获取支持的链、Gas价格、预估Gas Limit、广播交易以及查询广播订单等功能。
    所有方法都需要在 Config 对象中提供有效的 API Key, Secret Key 和 Passphrase。
    """
    API_VERSION_PATH = "/api/v5"
    # 注意基础路径与其他模块不同
    PRE_TRANSACTION_BASE_PATH = "/dex/pre-transaction"
    POST_TRANSACTION_BASE_PATH = "/dex/post-transaction" 

    def __init__(self, config: Config):
        """
        初始化 OnChainGateway。

        Args:
            config: SDK的配置实例。必须包含 API_KEY, SECRET_KEY, PASSPHRASE。
        Raises:
            ValueError: 如果配置中缺少API认证信息。
        """
        if not (config and config.API_KEY and config.SECRET_KEY and config.PASSPHRASE):
            raise ValueError("OnChainGateway 需要 Config 对象提供 API_KEY, SECRET_KEY, 和 PASSPHRASE。")
        self.config = config

    def _get_full_endpoint(self, base_path_type: str, specific_path: str) -> str:
        """ 构建完整的API endpoint路径。 """
        actual_base_path = ""
        if base_path_type == "pre_transaction":
            actual_base_path = self.PRE_TRANSACTION_BASE_PATH
        elif base_path_type == "post_transaction":
            actual_base_path = self.POST_TRANSACTION_BASE_PATH
        else:
            raise ValueError(f"未知的 base_path_type: {base_path_type}")
        return f"{self.API_VERSION_PATH}{actual_base_path}{specific_path}"

    def get_supported_chains(self) -> List[Dict[str, Any]]:
        """
        获取交易上链 API 支持的链信息。
        对应API: GET /api/v5/dex/pre-transaction/supported/chain
        """
        endpoint = self._get_full_endpoint("pre_transaction", "/supported/chain")
        response = make_request(method="GET", endpoint=endpoint, config=self.config)
        return response.get('data', [])

    def get_gas_price(self, chain_index: str) -> List[Dict[str, Any]]: # 文档显示data是list
        """
        动态获取指定链的预估 gasPrice。
        对应API: GET /api/v5/dex/pre-transaction/gas-price
        Args:
            chain_index: 链的唯一标识。
        """
        if not chain_index:
            raise ValueError("chain_index 不能为空")
        endpoint = self._get_full_endpoint("pre_transaction", "/gas-price")
        params = {"chainIndex": chain_index}
        response = make_request(method="GET", endpoint=endpoint, params=params, config=self.config)
        return response.get('data', [])

    def get_gas_limit(
        self,
        chain_index: str,
        from_address: str,
        to_address: str,
        tx_amount: Optional[str] = None,
        input_data: Optional[str] = None # calldata
    ) -> List[Dict[str, Any]]: # 文档显示data是list
        """
        通过交易信息的预执行，获取预估消耗的 Gaslimit (交易模拟)。
        对应API: POST /api/v5/dex/pre-transaction/gas-limit
        """
        if not all([chain_index, from_address, to_address]):
            raise ValueError("chain_index, from_address, to_address 不能为空")
        
        endpoint = self._get_full_endpoint("pre_transaction", "/gas-limit")
        json_body: Dict[str, Any] = {
            "chainIndex": chain_index,
            "fromAddr": from_address, # 注意API文档参数名 fromAddr, toAddr
            "toAddr": to_address
        }
        if tx_amount is not None: # API说默认"0", 如果不传会怎样？为安全起见，用户不传我们也不传
            json_body["txAmount"] = tx_amount
        if input_data is not None:
            json_body["extJson"] = {"inputData": input_data}
        
        response = make_request(method="POST", endpoint=endpoint, json_data=json_body, config=self.config)
        return response.get('data', [])

    def broadcast_transaction(
        self, 
        signed_tx: str, 
        chain_index: str, 
        address: str
    ) -> List[Dict[str, Any]]: # 文档显示data是list, 包含orderId
        """
        将已签名的交易广播到链上。
        注意: 此API可能仅向企业客户提供。
        对应API: POST /api/v5/dex/pre-transaction/broadcast-transaction
        """
        if not all([signed_tx, chain_index, address]):
            raise ValueError("signed_tx, chain_index, address 不能为空")
            
        endpoint = self._get_full_endpoint("pre_transaction", "/broadcast-transaction")
        json_body = {
            "signedTx": signed_tx,
            "chainIndex": chain_index,
            "address": address
        }
        response = make_request(method="POST", endpoint=endpoint, json_data=json_body, config=self.config)
        return response.get('data', [])

    def get_broadcast_orders(
        self, 
        address: str, 
        chain_index: str, 
        cursor: Optional[str] = None
    ) -> List[Dict[str, Any]]: # 文档显示data是list
        """
        查询指定地址和链的已广播交易订单列表。
        对应API: GET /api/v5/dex/post-transaction/orders
        """
        if not all([address, chain_index]):
            raise ValueError("address, chain_index 不能为空")

        endpoint = self._get_full_endpoint("post_transaction", "/orders")
        params: Dict[str, Any] = {"address": address, "chainIndex": chain_index}
        if cursor:
            params["cursor"] = cursor
        
        response = make_request(method="GET", endpoint=endpoint, params=params, config=self.config)
        return response.get('data', []) 