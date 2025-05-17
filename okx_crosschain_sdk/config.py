# okx_crosschain_sdk/config.py

class Config:
    """
    SDK配置类，用于存储和管理SDK的全局设置。
    """
    # OKX API 的基础URL
    BASE_API_URL = "https://web3.okx.com"

    # API 版本路径 (根据实际API调整，例如 /api/v5)
    API_VERSION_PATH = "/api/v5"

    # 完整的API端点基础
    @property
    def full_base_url(self):
        return f"{self.BASE_API_URL}{self.API_VERSION_PATH}"

    # 未来可以添加 API Key, Secret Key, Passphrase 等
    # API_KEY = None
    # SECRET_KEY = None
    # PASSPHRASE = None
    # PROJECT_ID = None # 有些API示例中提到了 OK-ACCESS-PROJECT

    # 请求超时时间 (秒)
    TIMEOUT = 30

def get_default_config():
    """
    获取一个默认的配置实例。
    """
    return Config()

# 你可以在这里创建一个默认的配置实例供整个SDK使用
# default_config = get_default_config() 