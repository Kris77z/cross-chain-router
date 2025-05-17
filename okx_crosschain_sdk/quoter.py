from typing import Optional, Literal, List, Dict, Any # For type hinting
from .config import Config, get_default_config
from .http_client import make_request, APIError

class Quoter:
    """
    跨链询价模块。
    用于根据用户输入获取OKX DEX跨链交易的最佳路径和报价。
    """
    def __init__(self, config: Config = None):
        """
        初始化 Quoter。

        Args:
            config: SDK的配置实例。如果为None，则使用默认配置。
        """
        self.config = config if config else get_default_config()
        self.base_endpoint = "/dex/cross-chain" # 基础路径

    def get_quote(
        self,
        from_chain_id: str,
        to_chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        user_address: Optional[str] = None,
        slippage: Optional[str] = None, # e.g., "0.5" for 0.5%
        receiver: Optional[str] = None,
        gas_price: Optional[str] = None, # e.g., "10000000000" for 10 Gwei
        quote_type: Optional[Literal["exactIn", "exactOut"]] = "exactIn",
        auto_slippage: Optional[bool] = False,
        preference: Optional[Literal["price", "speed"]] = None
    ) -> List[Dict[str, Any]]: # API 通常在 data 字段返回一个路由列表
        """
        获取跨链交易的路径和报价信息。

        对应API: /api/v5/dex/cross-chain/quote
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#获取路径信息

        Args:
            from_chain_id: 源链ID。
            to_chain_id: 目标链ID。
            from_token_address: 源链代币合约地址。
            to_token_address: 目标链代币合约地址。
            amount: 交易数量 (源链代币的最小单位数量)。
            user_address: (可选) 用户钱包地址。
            slippage: (可选) 滑点百分比，如 "0.5"。
            receiver: (可选) 目标链上的接收地址，默认为user_address。
            gas_price: (可选) 源链交易的gasPrice (wei)。
            quote_type: (可选) 报价类型，"exactIn" (默认) 或 "exactOut"。
            auto_slippage: (可选) 是否使用推荐滑点，默认为 false。
            preference: (可选) 偏好设置，"price" (价格最优) 或 "speed" (速度最快)。

        Returns:
            一个包含路由和报价信息的字典列表。通常，如果找到路径，列表的第一个元素是最优路径。
            例如API响应中的 `data` 字段。
            [
                {
                    "fromChainId": "1",
                    "toChainId": "137",
                    "fromTokenAddress": "0x0000000000000000000000000000000000000000",
                    "toTokenAddress": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
                    "userAddress": "0xYourUserAddress",
                    "amount": "10000000000000000", // 0.01 ETH
                    "slippage": "0.5",
                    "receiver": "0xYourUserAddress",
                    // ... 更多报价详情，如 estimatedAmount, fee, bridgeName, etc.
                }
            ]

        Raises:
            ValueError: 如果必填参数缺失。
            APIError: 如果API请求失败。
        """
        if not all([from_chain_id, to_chain_id, from_token_address, to_token_address, amount]):
            raise ValueError("参数 from_chain_id, to_chain_id, from_token_address, to_token_address, amount 不能为空")

        endpoint = f"{self.base_endpoint}/quote"
        
        params = {
            "fromChainId": from_chain_id,
            "toChainId": to_chain_id,
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": amount,
            "quoteType": quote_type,
            "autoSlippage": str(auto_slippage).lower() # API期望字符串 "true"/"false"
        }

        if user_address: params["userAddress"] = user_address
        if slippage: params["slippage"] = slippage
        if receiver: params["receiver"] = receiver
        if gas_price: params["gasPrice"] = gas_price
        if preference: params["preference"] = preference
        
        try:
            response_json = make_request(
                method='GET', # /quote 是 GET 请求
                endpoint=endpoint,
                params=params,
                config=self.config
            )
            
            # API成功时，`data` 字段应包含一个路由对象列表
            if 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            # 如果 data 是 null 但 code 是 0，表示没有找到路由
            elif 'data' in response_json and response_json['data'] is None and response_json.get('code') == '0':
                return [] # 返回空列表表示没有找到路径/报价
            else:
                raise APIError(
                    message=f"API响应格式错误或未找到报价信息: {endpoint}",
                    response_data=response_json
                )
        except APIError as e:
            # print(f"获取报价时发生错误: {e}")
            raise

# 简单使用示例 (用于测试)
# if __name__ == '__main__':
#     from okx_crosschain_sdk import Config, APIError # 假设 __init__.py 已配置
#     try:
#         # 请确保您有一个有效的配置，如果API需要密钥的话
#         # custom_config = Config()
#         # quoter = Quoter(config=custom_config)
#         quoter = Quoter()

#         # 示例参数 (请替换为有效的测试参数)
#         quote_params = {
#             "from_chain_id": "1",  # Ethereum
#             "to_chain_id": "10",   # Optimism
#             "from_token_address": "0x0000000000000000000000000000000000000000", # ETH
#             "to_token_address": "0x4200000000000000000000000000000000000006", # WETH on Optimism
#             "amount": "10000000000000000",  # 0.01 ETH in wei
#             "user_address": "0xYourWalletAddress" # 替换为您的钱包地址
#         }
#         print(f"正在获取报价，参数: {quote_params}")
#         routes = quoter.get_quote(**quote_params)

#         if routes:
#             print(f"\n成功获取到 {len(routes)} 条路由/报价:")
#             for i, route in enumerate(routes):
#                 print(f"--- 路由 {i+1} ---")
#                 print(f"  预计收到: {route.get('estimatedAmount')} {route.get('toTokenSymbol')}")
#                 print(f"  桥名称: {route.get('bridgeName')}")
#                 print(f"  总费用 (USD): {route.get('totalFeeUsd')}")
#                 print(f"  路由类型: {route.get('routeType')}")
#                 # print(f"  详细信息: {route}")
#         else:
#             print("\n未能找到任何路由/报价。")

#     except ValueError as e:
#         print(f"\n参数错误: {e}")
#     except APIError as e:
#         print(f"\nAPI错误: {e}")
#         print(f"  错误详情 - 状态码: {e.status_code}, 响应: {e.response_data}")
#     except Exception as e:
#         print(f"\n发生未知错误: {e}") 