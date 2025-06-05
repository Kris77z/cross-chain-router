# okx_crosschain_sdk/http_client.py
import requests
import json
import time
import hmac
import hashlib
import base64
from urllib.parse import urlparse, urlencode # Added urlencode for GET params in requestPath
from datetime import datetime

from .config import Config, get_default_config

class APIError(Exception):
    """自定义API错误异常，用于封装API请求中发生的错误。"""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self):
        return f"APIError: {self.args[0]} (Status Code: {self.status_code}, Response: {self.response_data})"

def _generate_signature(config: Config, method: str, request_path: str, body_str: str = "") -> tuple[str, str]:
    """
    生成OKX API所需的签名。
    """
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    prehash_str = timestamp + method.upper() + request_path + body_str
    
    mac = hmac.new(config.SECRET_KEY.encode('utf-8'), prehash_str.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(mac.digest()).decode('utf-8')
    
    return signature, timestamp

def make_request(
    method: str,
    # endpoint 现在是API的路径部分，例如 /dex/cross-chain/quote 或 /dex/pre-transaction/gas-price
    # 它不包含主机名，但应包含 /api/v5 (如果适用，或者由config.API_VERSION_PATH提供)
    endpoint: str,
    config: Config = None,
    params: dict = None,
    json_data: dict = None,
    headers: dict = None,
    extra_headers: dict = None  # 新增：额外的头部，用于特殊API如钱包API
):
    """
    发送HTTP请求到OKX API。
    """
    if config is None:
        config = get_default_config()

    # 构建完整的URL和用于签名的request_path
    # config.BASE_API_URL = "https://web3.okx.com"
    # config.API_VERSION_PATH = "/api/v5"
    # endpoint 应该是类似 "/dex/cross-chain/quote" 或 "/dex/pre-transaction/gas-price"
    
    # request_path_for_sign 需要包含 API_VERSION_PATH 和 endpoint
    # full_url 也需要它们
    
    # 确保 endpoint 不以 / 开头，如果 API_VERSION_PATH 已经是 /api/v5
    # 或者确保两者拼接时不会出现 //
    # 为了简单和明确，我们约定传给 make_request 的 endpoint 就已经是 /api/v5/dex/... 这样的形式
    # 这样 config 中就不再需要 API_VERSION_PATH 了。
    # 我将回退 Config 的修改，并让调用方负责传入完整的 /api/v5/... 路径作为 endpoint。

    # --- 修正思路：make_request 的 endpoint 参数应该是从 /api/v5 开始的完整路径 ---
    # 例如: "/api/v5/dex/cross-chain/quote"
    #       "/api/v5/dex/pre-transaction/gas-price"
    # config.BASE_API_URL 只是 "https://web3.okx.com"
    
    full_url_for_request = f"{config.BASE_API_URL}{endpoint}"
    request_path_for_sign = endpoint # endpoint 已经是 /api/v5/...

    if method.upper() == 'GET' and params:
        query_string = urlencode(params)
        full_url_for_request += f"?{query_string}"
        request_path_for_sign += f"?{query_string}" # GET的参数是requestPath的一部分

    body_str_for_sign = ""
    if method.upper() == 'POST' and json_data:
        # 对于POST，原始请求体参与签名
        body_str_for_sign = json.dumps(json_data)


    merged_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'OKXCrossChainSDK/0.0.1 (Python)' 
    }
    if headers:
        merged_headers.update(headers)

    if extra_headers:
        merged_headers.update(extra_headers)

    needs_auth = (config.API_KEY and config.SECRET_KEY and config.PASSPHRASE and
                  ("/dex/pre-transaction/" in endpoint or 
                   "/dex/post-transaction/" in endpoint or
                   "/dex/cross-chain/" in endpoint or
                   "/dex/aggregator/" in endpoint or
                   "/wallet/" in endpoint))  # 添加钱包API认证

    if needs_auth:
        if not config.SECRET_KEY:
             raise ValueError("SECRET_KEY is required for authenticated requests.")
        
        timestamp_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # 预签名字符串: timestamp + method + requestPath + body
        prehash_str = timestamp_iso + method.upper() + request_path_for_sign + body_str_for_sign

        hmac_obj = hmac.new(config.SECRET_KEY.encode('utf-8'), prehash_str.encode('utf-8'), hashlib.sha256)
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')

        merged_headers['OK-ACCESS-KEY'] = config.API_KEY
        merged_headers['OK-ACCESS-SIGN'] = signature
        merged_headers['OK-ACCESS-TIMESTAMP'] = timestamp_iso
        merged_headers['OK-ACCESS-PASSPHRASE'] = config.PASSPHRASE

    try:
        response = requests.request(
            method=method.upper(),
            url=full_url_for_request, 
            params=None if method.upper() == 'GET' else params, 
            json=json_data if method.upper() == 'POST' else None,
            headers=merged_headers,
            timeout=config.TIMEOUT
        )

        response.raise_for_status()

        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            raise APIError(
                message=f"无法解析JSON响应: {e}", 
                status_code=response.status_code, 
                response_data=response.text
            )
        
        if 'code' in response_json and response_json['code'] != '0':
            error_msg = response_json.get('msg', '未知API业务错误')
            if not error_msg and 'detailMsg' in response_json: # 有些接口detailMsg更详细
                error_msg = response_json['detailMsg']
            elif not error_msg and 'sMsg' in response_json: # 比如 /quote 接口用 sMsg
                 error_msg = response_json['sMsg']
            
            # 特殊处理 /quote 接口返回的 {"code":"0", "sCode":"51008", "sMsg":"...", "data":null} 情况
            # 它的外层code是"0"，但内部sCode非"0"表示错误
            if response_json['code'] == '0' and 'sCode' in response_json and response_json['sCode'] != '0':
                 error_msg_quote = response_json.get('sMsg', '未知 /quote API 业务错误')
                 raise APIError(
                    message=f"API业务错误 (from /quote): {error_msg_quote} (API sCode: {response_json['sCode']})",
                    status_code=response.status_code,
                    response_data=response_json
                )
            elif response_json['code'] != '0': # 其他接口的标准错误判断
                raise APIError(
                    message=f"API业务错误: {error_msg} (API Code: {response_json['code']})",
                    status_code=response.status_code,
                    response_data=response_json
                )

        return response_json

    except requests.exceptions.HTTPError as e:
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
        raise APIError(message=f"网络请求错误: {e}") 