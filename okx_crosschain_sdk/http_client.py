# okx_crosschain_sdk/http_client.py
import requests
import json
from .config import Config, get_default_config

class APIError(Exception):
    """自定义API错误异常，用于封装API请求中发生的错误。"""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self):
        return f"APIError: {self.args[0]} (Status Code: {self.status_code}, Response: {self.response_data})"

def make_request(
    method: str,
    endpoint: str,
    config: Config = None,
    params: dict = None,
    json_data: dict = None,
    headers: dict = None
):
    """
    发送HTTP请求到OKX API。

    Args:
        method: HTTP方法 (e.g., 'GET', 'POST').
        endpoint: API的端点路径 (e.g., '/dex/cross-chain/supported-chain').
        config: SDK的配置实例。如果为None，则使用默认配置。
        params: GET请求的查询参数。
        json_data: POST请求的JSON body。
        headers: 自定义的请求头。

    Returns:
        API响应的JSON数据 (dict)。

    Raises:
        APIError: 如果请求失败或响应状态码表示错误。
        requests.exceptions.RequestException: 如果发生网络层面的错误。
    """
    if config is None:
        config = get_default_config()

    full_url = f"{config.full_base_url}{endpoint}"

    merged_headers = {
        'Content-Type': 'application/json',
        # OKX API 可能需要其他特定的头部信息，例如API Key相关的
        # 'OK-ACCESS-KEY': config.API_KEY,
        # 'OK-ACCESS-TIMESTAMP': ...,
        # 'OK-ACCESS-SIGN': ...,
        # 'OK-ACCESS-PASSPHRASE': config.PASSPHRASE,
        # 'OK-ACCESS-PROJECT': config.PROJECT_ID, (示例中见过这个)
        'User-Agent': 'OKXCrossChainSDK/0.0.1 (Python)' # 最好标识我们的SDK
    }
    if headers:
        merged_headers.update(headers)

    try:
        response = requests.request(
            method=method.upper(),
            url=full_url,
            params=params,
            json=json_data,
            headers=merged_headers,
            timeout=config.TIMEOUT
        )

        # 检查HTTP错误状态码 (4xx, 5xx)
        response.raise_for_status()

        # 尝试解析JSON响应
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            raise APIError(
                message=f"无法解析JSON响应: {e}", 
                status_code=response.status_code, 
                response_data=response.text
            )
        
        # 根据OKX API的通用响应格式，检查业务错误码
        # 通常，OKX API会在 code 字段返回 '0' 表示成功
        # 例如: {"code":"0","msg":"","data":{...}} 或 {"code":"51000","msg":"Parameter error","data":[]}
        if 'code' in response_json and response_json['code'] != '0':
            error_msg = response_json.get('msg', '未知API业务错误')
            # 有些接口的错误信息可能在 detailMsg
            if not error_msg and 'detailMsg' in response_json:
                error_msg = response_json['detailMsg']
            raise APIError(
                message=f"API业务错误: {error_msg} (API Code: {response_json['code']})",
                status_code=response.status_code,
                response_data=response_json
            )

        return response_json

    except requests.exceptions.HTTPError as e:
        # HTTPError 已经包含了 response 对象
        error_response_text = e.response.text if e.response else 'No response body'
        try:
            error_response_json = e.response.json() if e.response else None
        except json.JSONDecodeError:
            error_response_json = error_response_text
        raise APIError(
            message=f"HTTP错误: {e}", 
            status_code=e.response.status_code if e.response else None, 
            response_data=error_response_json
        )
    except requests.exceptions.RequestException as e:
        # 其他网络层面的错误 (e.g., ConnectionError, Timeout)
        raise APIError(message=f"网络请求错误: {e}") 