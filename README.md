# OKX DEX 跨链 SDK (非官方)

__version__ = "0.0.1"

## 1. 项目目标

本项目旨在基于欧易（OKX）DEX 提供的跨链 API ([https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-cross-chain-api-introduction](https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-cross-chain-api-introduction)) 封装一个非官方的Python软件开发工具包 (SDK)。

主要目标包括：

*   **简化集成**：为开发者提供一个比直接调用 HTTP API 更易用、更友好的接口，方便将其集成到自己的交易系统或其他应用中。
*   **增强路由发现**：致力于通过灵活的参数配置和对 API 响应的细致处理，辅助用户发现OKX X-Routing算法提供的更全面的跨链交易路径，旨在解决官方前端可能存在的某些可行路径未显示的问题。
*   **提升开发效率**：封装底层的API调用、参数处理、错误处理等通用逻辑，提供清晰的模块化结构。

## 2. 与官方SDK的关系

我们注意到OKX官方提供了一个 `@okx-dex/okx-dex-sdk` ([https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-use-swap-solana-quick-start](https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-use-swap-solana-quick-start))，该SDK主要侧重于**单一区块链内**的代币兑换功能。

本SDK项目则专注于OKX的**跨链交易HTTP API**，旨在提供一个专门针对跨链场景的Python解决方案。如果未来OKX发布了官方的Python跨链SDK，我们将评估其功能，并可能调整本项目的方向。

## 3. SDK架构

SDK的核心将围绕OKX跨链API的主要流程进行设计，包含以下主要模块：

*   **`Config` (配置类)**
    *   用途：管理API基础URL、API版本、请求超时时间等全局配置。
    *   定义于：`okx_crosschain_sdk/config.py`

*   **`APIError` (自定义异常类)**
    *   用途：统一封装SDK中发生的API请求错误和业务逻辑错误。
    *   定义于：`okx_crosschain_sdk/http_client.py`

*   **`AssetExplorer` (资产与链信息模块)**
    *   用途：查询OKX DEX支持的跨链网络、代币信息、项目方配置代币和桥信息。
    *   对应API：
        *   `/api/v5/dex/cross-chain/supported-chain` (获取支持的链)
        *   `/api/v5/dex/cross-chain/token-list` (获取币种列表)
        *   `/api/v5/dex/cross-chain/configured-token-list` (获取项目方配置的币种列表)
        *   `/api/v5/dex/cross-chain/bridge-info` (获取支持的桥信息)
    *   实现于：`okx_crosschain_sdk/asset_explorer.py`

*   **`Quoter` (询价模块)**
    *   用途：核心模块，根据用户指定的源链、目标链、代币、金额等信息，调用OKX API获取最优的跨链路径和报价。这是实现"智能路由"的关键部分。
    *   对应API： `/api/v5/dex/cross-chain/quote` (获取路径信息/询价)
    *   实现于：`okx_crosschain_sdk/quoter.py`

*   **`TransactionBuilder` (交易构建模块)**
    *   用途：根据询价模块 (`Quoter`) 返回的选定路由信息，生成进行链上交互（如ERC20代币授权、执行实际跨链交易）所需的数据。
    *   对应API：
        *   `/api/v5/dex/cross-chain/approve-transaction` (获取授权交易数据)
        *   `/api/v5/dex/cross-chain/build-tx` (获取跨链兑换交易数据)
    *   实现于：`okx_crosschain_sdk/transaction_builder.py`

*   **`StatusTracker` (交易状态追踪模块)**
    *   用途：根据OKX API返回的内部交易ID (`txId`) 查询跨链交易的执行状态。
    *   对应API： `/api/v5/dex/cross-chain/status` (查询交易状态)
    *   实现于：`okx_crosschain_sdk/status_tracker.py`

*   内部辅助模块：
    *   `http_client.py`: 包含 `make_request` 函数，负责所有底层的HTTP请求发送、响应处理和基础错误检查。

## 4. 核心功能与特点

*   **全面的资产信息查询**：轻松获取所有支持的链、代币、项目方配置代币及桥信息。
*   **智能跨链询价**：通过灵活的参数组合调用 `/quote` 接口，获取OKX X-Routing提供的最佳交易方案，包括复杂的 "源链Swap + Bridge + 目标链Swap" 路径。
*   **便捷的交易构建**：简化获取ERC20授权数据和实际跨链交易数据的过程。
*   **实时的状态跟踪**：方便地根据OKX内部交易ID查询跨链交易的进展。
*   **清晰的错误处理**：通过自定义的 `APIError` 异常，提供具体的错误信息。
*   **模块化设计**：各功能模块职责分明，易于理解和扩展。

## 5. "智能路由"策略探讨

本SDK的"智能路由"主要依赖于OKX DEX跨链API中 `/quote` 接口内置的X-Routing算法。该算法旨在聚合多个DEX和跨链桥的流动性，自动计算最优路径。

SDK将通过以下方式辅助增强路由发现：

*   **参数组合的灵活性**：`Quoter` 模块允许用户传入所有 `/quote` API支持的参数，包括滑点、接收地址、gasPrice、报价类型、偏好（价格/速度）等，以便进行精细化的询价。
*   **结果的完整解析**：SDK确保从 `/quote` API返回的所有潜在路由信息（如果API支持返回多个选项，通常返回一个列表，第一个为最优）都能被完整捕获和呈现给用户。
*   **辅助用户决策**：虽然SDK本身不主动进行过于复杂的路径分段查询（因为这已是X-Routing的职责），但它提供了必要的信息获取工具（如 `AssetExplorer`），用户可以结合这些信息和 `Quoter` 的结果，制定自己的高级路由策略。

## 6. 使用方法

以下是如何使用本SDK进行跨链操作的基本流程和代码示例。

**安装 (假设未来发布到PyPI):**
```bash
# pip install okx-crosschain-sdk
```
目前请直接将 `okx_crosschain_sdk` 目录放置在您的项目路径下。

**6.1 初始化SDK模块:**

```python
from okx_crosschain_sdk import (
    Config,
    AssetExplorer,
    Quoter,
    TransactionBuilder,
    StatusTracker,
    APIError
)

# 使用默认配置初始化各个模块
# config = Config() # 如果需要修改默认配置，可以先创建Config实例
# asset_explorer = AssetExplorer(config=config)
# quoter = Quoter(config=config)
# tx_builder = TransactionBuilder(config=config)
# status_tracker = StatusTracker(config=config)

# 或者直接使用默认配置
asset_explorer = AssetExplorer()
quoter = Quoter()
tx_builder = TransactionBuilder()
status_tracker = StatusTracker()

print("OKX Cross-Chain SDK 初始化完毕!")
```

**6.2 获取基础信息 (可选):**

```python
try:
    print("\n--- 1. 获取支持的链信息 ---")
    supported_chains = asset_explorer.get_supported_chains()
    if supported_chains:
        print(f"获取到 {len(supported_chains)} 条支持的链。例如: {supported_chains[0].get('chainName')}")
        # for chain in supported_chains:
        #     print(f"  - {chain.get('chainName')} (ID: {chain.get('chainId')})")

        # 获取第一条链的代币列表作为示例
        example_chain_id = supported_chains[0].get('chainId')
        if example_chain_id:
            print(f"\n--- 2. 获取链 {supported_chains[0].get('chainName')} (ID: {example_chain_id}) 的代币列表 ---")
            tokens_on_chain = asset_explorer.get_token_list(chain_id=example_chain_id)
            if tokens_on_chain:
                print(f"获取到 {len(tokens_on_chain)} 种代币。例如: {tokens_on_chain[0].get('tokenSymbol')}")
            else:
                print(f"链 {example_chain_id} 上没有代币或获取失败。")
    else:
        print("未能获取支持的链列表。")

except APIError as e:
    print(f"获取基础信息时发生API错误: {e}")
```

**6.3 进行跨链询价:**

```python
# 替换为实际的测试参数
YOUR_WALLET_ADDRESS = "0xYourWalletAddressHere" # 非常重要：替换为您的测试钱包地址

quote_params = {
    "from_chain_id": "1",  # Ethereum
    "to_chain_id": "10",   # Optimism
    "from_token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", # USDC on Ethereum
    "to_token_address": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",   # USDC on Optimism
    "amount": "1000000",  # 1 USDC (假设USDC是6位小数)
    "user_address": YOUR_WALLET_ADDRESS,
    "slippage": "0.5", # 0.5%
    # "preference": "speed" # 可选：偏好速度或价格
}

selected_route = None # 用于存储选中的路由信息

try:
    print(f"\n--- 3. 进行跨链询价 ({quote_params.get('from_token_address')} -> {quote_params.get('to_token_address')}) ---")
    available_routes = quoter.get_quote(**quote_params)
    
    if available_routes:
        selected_route = available_routes[0] # 通常API返回的第一个是推荐/最优路由
        print(f"成功获取到 {len(available_routes)} 条路由报价。")
        print(f"  最优路由预计通过 {selected_route.get('bridgeName')} 桥接。")
        print(f"  发送 {selected_route.get('fromTokenAmount')} {selected_route.get('fromTokenSymbol")} "
              f"预计收到: {selected_route.get('estimatedAmount')} {selected_route.get('toTokenSymbol')}")
        print(f"  预计总费用 (USD): {selected_route.get('totalFeeUsd')}")
        print(f"  是否需要授权: {selected_route.get('transactionData', {}).get('needApprove')}")
    else:
        print("未能找到可用的跨链路由报价。")

except APIError as e:
    print(f"询价时发生API错误: {e}")
except ValueError as e:
    print(f"询价参数错误: {e}")
```

**6.4 获取交易数据 (授权和执行):**

```python
approve_calldata = None
built_tx_calldata = None
okx_internal_tx_id = None # 用于后续状态查询

if selected_route:
    try:
        # 6.4.1 获取授权交易数据 (如果需要)
        # 注意: selected_route['transactionData']['needApprove'] 在实际路由数据中获取
        if selected_route.get("transactionData", {}).get("needApprove") is True:
            print("\n--- 4.1 获取ERC20授权交易数据 ---")
            # 这里的 route_data 就是上面询价得到的 selected_route
            approve_data = tx_builder.get_approve_transaction_data(route_data=selected_route)
            print(f"  授权交易发送到 (代币合约): {approve_data.get('to')}")
            print(f"  授权交易数据 (calldata): {approve_data.get('data')[:60]}...")
            approve_calldata = approve_data # 保存以备后续模拟发送
            # 在实际应用中, 你需要将此 approve_data 签名并发送到源链网络
            # 然后等待交易确认，获取授权交易的哈希 (approve_tx_hash)
            mock_approve_tx_hash = "0x_mock_approve_tx_hash_for_testing" # 模拟
            print(f"  (模拟) 授权交易已发送，哈希: {mock_approve_tx_hash}")
        else:
            print("\n--- 4.1 此路由无需ERC20授权或已授权 ---")
            mock_approve_tx_hash = None # 无需授权，则无授权哈希

        # 6.4.2 获取构建实际跨链交易的数据
        print("\n--- 4.2 获取构建实际跨链交易数据 ---")
        # 这里的 route_data 仍然是 selected_route
        # 如果有授权，可以将授权交易的 txId (哈希) 传给 build-tx 接口
        build_tx_data = tx_builder.get_build_transaction_data(
            route_data=selected_route,
            approve_tx_id=mock_approve_tx_hash # 如果上一步有授权哈希，则传入
            # gas_price="25000000000" # 可选：自定义gasPrice (单位: wei)
        )
        print(f"  实际跨链交易发送到 (路由合约): {build_tx_data.get('to')}")
        print(f"  交易金额 (value): {build_tx_data.get('value')}")
        print(f"  交易数据 (calldata): {build_tx_data.get('data')[:60]}...")
        print(f"  建议 Gas Price: {build_tx_data.get('gasPrice')}")
        print(f"  建议 Gas Limit: {build_tx_data.get('gasLimit')}")
        okx_internal_tx_id = build_tx_data.get('txId') # OKX内部订单ID，用于状态查询
        if okx_internal_tx_id:
            print(f"  获取到OKX内部交易ID (用于状态查询): {okx_internal_tx_id}")
        built_tx_calldata = build_tx_data # 保存以备后续模拟发送
        # 在实际应用中, 你需要将此 built_tx_data 签名并发送到源链网络
        # print("  (模拟) 实际跨链交易已发送!")

    except APIError as e:
        print(f"获取交易数据时发生API错误: {e}")
    except ValueError as e:
        print(f"获取交易数据时参数错误: {e}")
```

**6.5 查询交易状态:**

```python
if okx_internal_tx_id:
    try:
        print(f"\n--- 5. 查询交易状态 (OKX内部txId: {okx_internal_tx_id}) ---")
        # 实际中可能需要轮询查询状态
        import time
        time.sleep(5) # 等待几秒钟让后台处理
        
        status_info = status_tracker.get_transaction_status(tx_id=okx_internal_tx_id)
        
        if status_info:
            print(f"  当前交易状态: {status_info.get('state')}")
            print(f"  源链交易哈希: {status_info.get('fromTxHash')}")
            print(f"  目标链交易哈希: {status_info.get('toTxHash')}")
            print(f"  发送金额: {status_info.get('sendAmount')} {status_info.get('fromTokenSymbol')}")
            print(f"  接收金额: {status_info.get('receiveAmount')} {status_info.get('toTokenSymbol')}")
        else:
            print("未能获取到该交易的明确状态信息 (可能仍在处理或ID有误)。")
            
    except APIError as e:
        print(f"查询交易状态时发生API错误: {e}")
    except ValueError as e:
        print(f"查询交易状态时参数错误: {e}")
else:
    print("\n--- 5. 未能获取OKX内部交易ID，无法查询状态 ---")

```

## 7. 开发语言与环境

*   主要开发语言：Python 3.7+ (使用了f-string和类型提示)
*   运行环境：Python 3.7+
*   主要依赖： `requests` (用于HTTP请求)。 请通过 `pip install requests` 安装。

## 8. API认证说明

当前版本的SDK主要针对OKX DEX跨链API中不需要复杂头部认证（如签名、时间戳等）的公开端点。
OKX的某些其他API（例如，一些特定链的DEX Swap API的Node.js示例中）可能需要 `OK-ACCESS-KEY`, `OK-ACCESS-SIGN` 等头部进行认证。
如果未来发现跨链API的某些端点或特定场景也需要此类认证，SDK的 `http_client` 模块和 `Config` 类将需要扩展以支持生成这些认证头部。
目前，SDK的 `http_client` 中已预留相关注释位置。

## 9. 贡献与反馈

欢迎对本项目提出改进建议、报告问题或贡献代码。
*   问题反馈：请通过 [GitHub Issues (待创建)] 提交。
*   贡献代码：请遵循标准的 Fork & Pull Request 流程。

---
*免责声明：本项目为非官方SDK，依赖于OKX提供的公开API。API的可用性和功能变更由OKX决定。使用者应自行承担使用本SDK的风险。交易涉及风险，请谨慎操作。* 