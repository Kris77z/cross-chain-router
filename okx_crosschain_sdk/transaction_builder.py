from typing import Dict, Any, Optional
from .config import Config, get_default_config
from .http_client import make_request, APIError

class TransactionBuilder:
    """
    交易构建模块。
    负责获取构建授权交易和实际跨链交易所需的数据。
    """
    def __init__(self, config: Config = None):
        """
        初始化 TransactionBuilder。

        Args:
            config: SDK的配置实例。如果为None，则使用默认配置。
        """
        self.config = config if config else get_default_config()
        self.base_endpoint = "/dex/cross-chain" # 基础路径

    def get_approve_transaction_data(
        self,
        route_data: Dict[str, Any],
        # gas_price: Optional[str] = None # 通常approve的gasPrice由客户端最终设定
    ) -> Dict[str, Any]:
        """
        获取构建ERC20代币授权交易所需要的数据。
        对应API: /api/v5/dex/cross-chain/approve-transaction (POST请求)
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#交易授权
        Args:
            route_data: 从 Quoter.get_quote() 获取并选定的单个路由对象。
        Returns:
            一个包含授权交易所需数据的字典。
        Raises:
            ValueError: 如果 route_data 为空。
            APIError: 如果API请求失败。
        """
        if not route_data:
            raise ValueError("route_data 参数不能为空")

        endpoint = f"{self.base_endpoint}/approve-transaction"
        request_body = route_data.copy()

        try:
            response_json = make_request(
                method='POST',
                endpoint=endpoint,
                json_data=request_body,
                config=self.config
            )
            if 'data' in response_json:
                return response_json['data']
            else:
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'在 {endpoint}",
                    response_data=response_json
                )
        except APIError as e:
            raise

    def get_build_transaction_data(
        self,
        route_data: Dict[str, Any],
        approve_tx_id: Optional[str] = None, # 授权交易的哈希 (如果需要)
        gas_price: Optional[str] = None      # 用户期望用于此跨链交易的gasPrice
    ) -> Dict[str, Any]:
        """
        获取构建实际跨链兑换交易所需要的数据。

        对应API: /api/v5/dex/cross-chain/build-tx (POST请求)
        API文档: https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-crosschain-api#跨链兑换

        Args:
            route_data: 从 Quoter.get_quote() 获取并选定的单个路由对象。
            approve_tx_id: (可选) 如果此交易需要前置授权，则为授权交易的哈希 (txId)。
            gas_price: (可选) 用户希望用于此跨链交易的gasPrice (单位: wei)。

        Returns:
            一个包含实际跨链交易所需数据的字典，例如：
            {
                "to": "0xRouterAddress", // 跨链路由合约地址
                "data": "0xSwapData...",   // 跨链交易的calldata
                "value": "10000000000000000", // 如果发送原生代币，则为数量，否则为0
                "gasPrice": "12000000000",
                "gasLimit": "500000",
                "txId": "..." // API返回的内部订单ID或交易标识
                // ... 可能还有其他字段
            }

        Raises:
            ValueError: 如果 route_data 为空。
            APIError: 如果API请求失败。
        """
        if not route_data:
            raise ValueError("route_data 参数不能为空")

        endpoint = f"{self.base_endpoint}/build-tx"
        
        # API期望整个路由对象作为请求体，并可能包含额外的txId或gasPrice
        request_body = route_data.copy() # 复制以避免修改原始对象
        
        if approve_tx_id:
            request_body["txId"] = approve_tx_id # 根据文档，此为授权交易的hash
        
        if gas_price:
            # 文档明确提到可以在请求体中加入gasPrice
            request_body["gasPrice"] = gas_price
        
        try:
            response_json = make_request(
                method='POST',
                endpoint=endpoint,
                json_data=request_body, # 将路由对象及可能的额外参数作为JSON body发送
                config=self.config
            )
            
            # API成功时，`data` 字段应包含实际交易的数据
            if 'data' in response_json:
                return response_json['data']
            else:
                raise APIError(
                    message=f"API响应格式错误: 未找到'data'在 {endpoint}",
                    response_data=response_json
                )
        except APIError as e:
            raise

# 简单使用示例 (用于测试)
# if __name__ == '__main__':
#     from okx_crosschain_sdk import Quoter, APIError, Config # 假设 __init__.py 已配置
#     try:
#         # --- 配置 (如果需要API Key，请在此处设置) ---
#         # conf = Config()
#         # conf.API_KEY = "YOUR_API_KEY"
#         # conf.PASSPHRASE = "YOUR_PASSPHRASE"
#         # conf.SECRET_KEY = "YOUR_SECRET_KEY"
#         # quoter = Quoter(config=conf)
#         # tx_builder = TransactionBuilder(config=conf)
#         quoter = Quoter()
#         tx_builder = TransactionBuilder()

#         # --- 1. 获取报价 ---
#         quote_params = {
#             "from_chain_id": "1",  # Ethereum
#             "to_chain_id": "10",   # Optimism
#             "from_token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", # USDC on Ethereum
#             "to_token_address": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",   # USDC on Optimism
#             "amount": "1000000",  # 1 USDC (6 decimals for USDC)
#             "user_address": "YOUR_WALLET_ADDRESS_HERE" # 替换为您的钱包地址
#         }
#         print(f"正在获取报价，参数: {quote_params}")
#         routes = quoter.get_quote(**quote_params)

#         if not routes:
#             print("未能找到任何路由/报价，测试终止。")
#         else:
#             selected_route = routes[0] # 通常选择第一条作为最优路由
#             print(f"\n选择的路由: 来自 {selected_route.get('fromChainName')} 的 {selected_route.get('fromTokenSymbol')} "
#                   f"到 {selected_route.get('toChainName')} 的 {selected_route.get('toTokenSymbol')}")
#             print(f"  桥: {selected_route.get('bridgeName')}, 预计收到: {selected_route.get('estimatedAmount')}")

#             approve_tx_hash_if_any = None

#             # --- 2. (如果需要) 获取并模拟授权交易 ---
#             # 实际使用中，你需要检查 selected_route['transactionData']['needApprove']
#             # 这里我们假设它需要授权来进行演示
#             need_approve_flag = selected_route.get("transactionData", {}).get("needApprove")
#             if need_approve_flag is True:
#                 print("\n路由需要授权，正在获取授权交易数据...")
#                 approve_data_from_api = tx_builder.get_approve_transaction_data(route_data=selected_route)
#                 print("成功获取到授权交易数据:")
#                 print(f"  授权给 (代币合约): {approve_data_from_api.get('to')}")
#                 print(f"  授权Calldata: {approve_data_from_api.get('data')[:50]}...") # 打印部分calldata
#                 # 在实际应用中，你会发送这笔授权交易到链上，并获取其交易哈希
#                 approve_tx_hash_if_any = "0x_mock_approve_tx_hash_for_testing" # 模拟授权交易哈希
#                 print(f"模拟授权交易已发送，哈希: {approve_tx_hash_if_any}")
#             else:
#                 print("\n路由不需要授权，或 selected_route['transactionData']['needApprove'] 未明确为 true。跳过授权步骤。")
            
#             # --- 3. 获取构建实际跨链交易的数据 ---
#             print("\n正在获取构建实际跨链交易的数据...")
#             build_tx_payload = selected_route # 使用完整的路由信息作为基础
            
#             # 如果有授权交易哈希，添加到请求体中 (一些桥可能需要)
#             # approve_tx_hash_if_any = "" # 如果确定不需要，或者没有执行授权，则不传或传空

#             actual_cross_chain_tx_data = tx_builder.get_build_transaction_data(
#                 route_data=build_tx_payload,
#                 approve_tx_id=approve_tx_hash_if_any, # 如果有的话
#                 # gas_price="20000000000" # (可选) 覆盖gasPrice, e.g., 20 Gwei
#             )
#             print("\n成功获取到构建跨链交易的数据:")
#             print(f"  目标合约地址 (To): {actual_cross_chain_tx_data.get('to')}")
#             print(f"  交易金额 (Value): {actual_cross_chain_tx_data.get('value')}")
#             print(f"  交易Calldata: {actual_cross_chain_tx_data.get('data')[:50]}...") # 打印部分calldata
#             print(f"  建议 Gas Price: {actual_cross_chain_tx_data.get('gasPrice')}")
#             print(f"  建议 Gas Limit: {actual_cross_chain_tx_data.get('gasLimit')}")
#             print(f"  OKX内部交易ID (txId): {actual_cross_chain_tx_data.get('txId')}")

#     except ValueError as e:
#         print(f"\n参数错误: {e}")
#     except APIError as e:
#         print(f"\nAPI错误: {e}")
#         print(f"  错误详情 - 状态码: {e.status_code}, 响应: {e.response_data}")
#     except Exception as e:
#         print(f"\n发生未知错误: {e}") 