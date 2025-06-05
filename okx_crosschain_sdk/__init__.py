# okx_crosschain_sdk/__init__.py

"""OKX Cross-Chain SDK (Non-Official)

一个用于与OKX DEX跨链API交互的Python SDK。
"""

__version__ = "0.0.1" # SDK 版本号

# 从各个模块中导入主要的类，方便用户直接从SDK包导入
from .config import Config, get_default_config
from .http_client import APIError # make_request 一般不直接暴露给SDK用户
from .asset_explorer import AssetExplorer
from .quoter import Quoter
from .transaction_builder import TransactionBuilder
from .status_tracker import StatusTracker
from .onchain_gateway import OnChainGateway # 新增导入

# 未来可以添加其他模块的导入

# 控制 `from okx_crosschain_sdk import *` 的行为
# 推荐显式导入，但如果需要，可以在这里定义 __all__
__all__ = [
    'Config',
    'get_default_config',
    'APIError',
    'AssetExplorer',
    'Quoter',
    'TransactionBuilder',
    'StatusTracker',
    'OnChainGateway' # 新增到 __all__
] 