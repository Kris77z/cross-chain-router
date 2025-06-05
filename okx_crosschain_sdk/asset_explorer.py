from .config import Config, get_default_config
from .http_client import make_request, APIError
from typing import List, Dict

class AssetExplorer:
    """
    资产与链信息模块。
    用于查询OKX DEX支持的跨链网络、代币信息、桥信息等。
    """
    # API 版本和基础路径，用于构建完整的endpoint
    API_VERSION_PATH = "/api/v5"
    MODULE_BASE_PATH = "/dex/cross-chain"

    def __init__(self, config: Config = None):
        """
        初始化 AssetExplorer。

        Args:
            config: SDK的配置实例。如果为None，则使用默认配置。
        """
        self.config = config if config else get_default_config()

    def _get_full_endpoint(self, specific_path: str) -> str:
        """ 构建完整的API endpoint路径，包含版本和模块基础路径。 """
        return f"{self.API_VERSION_PATH}{self.MODULE_BASE_PATH}{specific_path}"

    def get_supported_chains(self, chain_index: str = None) -> list:
        """
        获取OKX DEX跨链支持的所有链信息。
        对应API: /api/v5/dex/cross-chain/supported/chain
        API文档: https://web3.okx.com/zh-hans/build/docs/waas/dex-get-supported-chains

        Args:
            chain_index: 可选，链的唯一标识。如1: Ethereum

        Returns:
            一个包含链信息的列表

        Raises:
            APIError: 如果API请求失败。
        """
        endpoint = self._get_full_endpoint("/supported/chain")
        params = {}
        if chain_index:
            params["chainIndex"] = chain_index
            
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                params=params if params else None,
                config=self.config
            )
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            else:
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'列表在 {endpoint}", 
                    response_data=response_json
                )
        except APIError as e:
            raise

    def get_token_list(self, chain_index: str = None) -> list:
        """
        获取欧易 DEX 聚合器协议支持兑换的币种列表。
        对应API: /api/v5/dex/aggregator/all-tokens

        Args:
            chain_index: 可选，链的唯一标识 (例如 "1" 代表 Ethereum)。

        Returns:
            一个包含代币信息的列表

        Raises:
            APIError: 如果API请求失败。
        """
        endpoint = "/api/v5/dex/aggregator/all-tokens"
        params = {}
        if chain_index:
            params["chainIndex"] = chain_index
        
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                params=params if params else None,
                config=self.config
            )
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            elif 'data' in response_json and response_json['data'] is None and response_json.get('code') == '0':
                return []
            else:
                raise APIError(
                    message=f"API响应格式错误或未找到对应 chainIndex 的代币列表: {endpoint} with chainIndex {chain_index}",
                    response_data=response_json
                )
        except APIError as e:
            raise

    def get_crosschain_tokens(self, chain_index: str = None) -> list:
        """
        获取仅通过跨链桥交易的币种列表。
        对应API: /api/v5/dex/cross-chain/supported/tokens

        Args:
            chain_index: 可选，链的唯一标识。

        Returns:
            一个包含跨链代币信息的列表。

        Raises:
            APIError: 如果API请求失败。
        """
        endpoint = self._get_full_endpoint("/supported/tokens")
        params = {}
        if chain_index:
            params["chainIndex"] = chain_index
            
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                params=params if params else None,
                config=self.config
            )
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            elif 'data' in response_json and response_json['data'] is None and response_json.get('code') == '0':
                return []
            else:
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'列表在 {endpoint}", 
                    response_data=response_json
                )
        except APIError as e:
            raise

    def get_configured_token_list(self) -> list:
        """
        获取项目方在DEX聚合器配置的币种列表。
        对应API: /api/v5/dex/cross-chain/configured-token-list
        """
        endpoint = self._get_full_endpoint("/configured-token-list")
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                config=self.config
            )
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            elif 'data' in response_json and response_json['data'] is None and response_json.get('code') == '0':
                return []
            else:
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'列表在 {endpoint}", 
                    response_data=response_json
                )
        except APIError as e:
            raise

    def get_bridge_info(self) -> list:
        """
        获取支持的桥信息。
        对应API: /api/v5/dex/cross-chain/supported/bridges
        """
        endpoint = self._get_full_endpoint("/supported/bridges")
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                config=self.config
            )
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            elif 'data' in response_json and response_json['data'] is None and response_json.get('code') == '0':
                return []
            else:
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'列表在 {endpoint}", 
                    response_data=response_json
                )
        except APIError as e:
            raise 