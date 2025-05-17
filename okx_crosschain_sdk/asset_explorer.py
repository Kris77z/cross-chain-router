from .config import Config, get_default_config
from .http_client import make_request, APIError

class AssetExplorer:
    """
    资产与链信息模块。
    用于查询OKX DEX支持的跨链网络、代币信息、桥信息等。
    """
    def __init__(self, config: Config = None):
        """
        初始化 AssetExplorer。

        Args:
            config: SDK的配置实例。如果为None，则使用默认配置。
        """
        self.config = config if config else get_default_config()
        self.base_endpoint = "/dex/cross-chain" # 基础路径，方便管理

    def get_supported_chains(self) -> list:
        """
        获取OKX DEX跨链支持的所有链信息。

        对应API: /api/v5/dex/cross-chain/supported-chain
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#获取支持的链

        Returns:
            一个包含链信息的列表，例如：
            [
                {
                    "chainId": "1",
                    "chainName": "Ethereum",
                    "chainFullName": "Ethereum",
                    "logoURI": "https://static.okx.com/cdn/wallet/logo/ Ethereum.png",
                    "isTestNet": false,
                    "explorerUrl": "https://etherscan.io/",
                    "crossChainFeeToken": "ETH",
                    "crossChainFeeTokenLogoURI": "https://static.okx.com/cdn/wallet/logo/ETH.png?x-oss-process=image/format,webp",
                    "minCrossChainFee": "0.001",
                    "maxCrossChainFee": "0.05"
                },
                ...
            ]

        Raises:
            APIError: 如果API请求失败。
        """
        endpoint = f"{self.base_endpoint}/supported-chain"
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                config=self.config
            )
            # 根据API文档，成功时数据在 response_json['data'] 中
            # 并且它是一个列表
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            else:
                # 如果'data'字段不存在或不是列表，这可能是一个非预期的响应格式
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'列表在 {endpoint}", 
                    response_data=response_json
                )
        except APIError as e:
            # 可以选择在这里记录日志或直接重新抛出
            # print(f"获取支持链信息时发生错误: {e}")
            raise # 重新抛出捕获的APIError

    def get_token_list(self, chain_id: str) -> list:
        """
        获取指定链上支持的代币（币种）列表。

        对应API: /api/v5/dex/cross-chain/token-list
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#获取币种列表

        Args:
            chain_id: 链的ID (例如 "1" 代表 Ethereum)。

        Returns:
            一个包含代币信息的列表，例如：
            [
                {
                    "tokenContractAddress": "0x0000000000000000000000000000000000000000",
                    "tokenSymbol": "ETH",
                    "tokenLogoURI": "https://static.okx.com/cdn/wallet/logo/ETH.png?x-oss-process=image/format,webp",
                    "tokenDecimals": "18",
                    "crossChainSupport": true,
                    "crossChainTokenContractAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                    "tokenName": "Ethereum",
                    "maxAmount": "100000",
                    "minAmount": "0.00001",
                    "mainNet": true
                },
                ...
            ]

        Raises:
            APIError: 如果API请求失败。
        """
        if not chain_id:
            raise ValueError("chain_id 参数不能为空")

        endpoint = f"{self.base_endpoint}/token-list"
        params = {"chainId": chain_id}
        
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                params=params,
                config=self.config
            )
            # 响应结构通常是 {"code": "0", "msg": "", "data": [{...}, {...}]}
            # data本身可能是一个包含不同链ID作为key的字典，每个key对应一个代币列表
            # 或者直接是对应 chain_id 的代币列表。根据文档示例，直接是代币列表。
            # https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#获取币种列表 的响应示例直接是data: [{token1}, {token2}]
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            # 有时候API对于没有数据的请求可能返回 data: null 或者 data: []
            # 如果data是null但code是0，也认为是成功但没有数据
            elif 'data' in response_json and response_json['data'] is None and response_json.get('code') == '0':
                return [] # 返回空列表表示没有代币
            else:
                raise APIError(
                    message=f"API响应格式错误或未找到对应 chainId 的代币列表: {endpoint} with chainId {chain_id}",
                    response_data=response_json
                )
        except APIError as e:
            raise

    def get_configured_token_list(self) -> list:
        """
        获取项目方在DEX聚合器配置的币种列表。
        这些币种在币列表中不一定存在。
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#获取项目方配置的币种列表
        Returns: list: 一个包含项目方配置代币信息的列表。
        Raises: APIError: 如果API请求失败。
        """
        endpoint = f"{self.base_endpoint}/configured-token-list"
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                config=self.config
            )
            # 文档显示响应: {"code":"0","msg":"","data":[{"chainId":"1",...}]}
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
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#获取支持的桥信息
        Returns: list: 一个包含桥信息的列表。
        Raises: APIError: 如果API请求失败。
        """
        endpoint = f"{self.base_endpoint}/bridge-info"
        try:
            response_json = make_request(
                method='GET',
                endpoint=endpoint,
                config=self.config
            )
            # 文档显示响应: {"code":"0","msg":"","data":[{"bridgeName":"cBridge V2",...}]}
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

# 简单使用示例 (用于测试, 实际使用时不会放在这里)
# if __name__ == '__main__':
#     from okx_crosschain_sdk import APIError # 假设__init__.py已配置
#     try:
#         explorer = AssetExplorer()
#         print("--- 获取支持的链 ---")
#         chains = explorer.get_supported_chains()
#         if chains:
#             print(f"获取到 {len(chains)} 条链的信息。第一条链: {chains[0].get('chainName')}")
#             # 获取第一条链的代币列表
#             first_chain_id = chains[0].get('chainId')
#             if first_chain_id:
#                 print(f"\n--- 获取链 {chains[0].get('chainName')} (ID: {first_chain_id}) 的代币列表 ---")
#                 tokens = explorer.get_token_list(chain_id=first_chain_id)
#                 if tokens:
#                     print(f"获取到 {len(tokens)} 种代币。第一种代币: {tokens[0].get('tokenSymbol')}")
#                 else:
#                     print(f"链 {first_chain_id} 上没有找到代币列表。")
#         else:
#             print("未能获取到支持的链列表。")

#         print("\n--- 获取项目方配置的代币列表 ---")
#         conf_tokens = explorer.get_configured_token_list()
#         if conf_tokens:
#             print(f"获取到 {len(conf_tokens)} 条项目方配置的代币信息。第一条: {conf_tokens[0]}")
#         else:
#             print("未能获取到项目方配置的代币列表或列表为空。")

#         print("\n--- 获取支持的桥信息 ---")
#         bridges = explorer.get_bridge_info()
#         if bridges:
#             print(f"获取到 {len(bridges)} 条桥信息。第一条: {bridges[0].get('bridgeName')}")
#         else:
#             print("未能获取到支持的桥列表或列表为空。")


    # except APIError as e:
    #     print(f"\n发生API错误: {e}")
    #     print(f"  错误详情 - 状态码: {e.status_code}, 响应: {e.response_data}")
    # except ValueError as e:
    #     print(f"\n发生参数错误: {e}")
    # except Exception as e:
    #     print(f"\n发生未知错误: {e}") 