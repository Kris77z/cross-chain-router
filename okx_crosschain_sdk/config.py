# okx_crosschain_sdk/config.py

class Config:
    """
    SDK配置类，用于存储和管理SDK的全局设置。
    """
    # OKX API 的主机URL
    BASE_API_URL = "https://web3.okx.com"

    # API_VERSION_PATH 不再需要，因为调用方会提供完整的endpoint路径，如 /api/v5/...
    # BASE_URL property 也不再需要

    # API 认证相关
    API_KEY: str = None
    SECRET_KEY: str = None
    PASSPHRASE: str = None

    # 请求超时时间 (秒)
    TIMEOUT: int = 30

    def __init__(self, api_key: str = None, secret_key: str = None, passphrase: str = None, timeout: int = 30):
        """
        初始化Config对象。

        Args:
            api_key: 您的OKX API Key。
            secret_key: 您的OKX API Secret Key。
            passphrase: 您的OKX API Passphrase。
            timeout: 请求超时时间（秒）。
        """
        if api_key:
            self.API_KEY = api_key
        if secret_key:
            self.SECRET_KEY = secret_key
        if passphrase:
            self.PASSPHRASE = passphrase
        self.TIMEOUT = timeout

def get_default_config():
    """
    获取一个默认的配置实例。
    """
    return Config()

# 你可以在这里创建一个默认的配置实例供整个SDK使用
# default_config = get_default_config() 