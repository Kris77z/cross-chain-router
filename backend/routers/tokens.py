"""
代币信息相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import sys
import os

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 使用绝对路径加载环境变量
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, '.env.local')
    load_dotenv(env_path)
    load_dotenv('.env')
except ImportError:
    pass

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from okx_crosschain_sdk import AssetExplorer, Config, APIError
except ImportError:
    AssetExplorer = None
    Config = None
    APIError = Exception

router = APIRouter()

# 依赖注入：获取AssetExplorer实例
def get_asset_explorer():
    if AssetExplorer is None:
        raise HTTPException(status_code=500, detail="OKX SDK未正确导入")
    
    # 从环境变量获取API Key配置
    api_key = os.getenv('OKX_API_KEY')
    secret_key = os.getenv('OKX_SECRET_KEY')
    passphrase = os.getenv('OKX_PASSPHRASE')
    
    # 如果有API Key配置，则使用认证配置，否则使用默认配置
    if api_key and secret_key and passphrase:
        config = Config(
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase
        )
    else:
        config = Config()
    
    return AssetExplorer(config)

@router.get("/{chain_id}", summary="获取特定链上的代币列表")
async def get_tokens_by_chain(
    chain_id: str,
    limit: Optional[int] = Query(100, description="返回代币数量限制"),
    search: Optional[str] = Query(None, description="搜索代币符号或名称"),
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
) -> List[Dict[str, Any]]:
    """
    获取特定区块链上支持的代币列表
    
    参数:
    - chain_id: 链ID (如 "1" 表示以太坊)
    - limit: 返回结果数量限制 (默认100)
    - search: 搜索关键词，可搜索代币符号或名称
    
    返回:
    - 代币列表，包含符号、名称、地址、图标等信息
    """
    try:
        print(f"📝 获取链 {chain_id} 的代币列表，限制: {limit}")
        
        # 调用SDK获取代币列表
        tokens = asset_explorer.get_token_list(chain_index=chain_id)
        
        if not tokens:
            print(f"⚠️ 链 {chain_id} 返回空代币列表")
            return []
        
        print(f"✅ 链 {chain_id} 获取到 {len(tokens)} 个代币")
        
        # 增强代币信息
        enhanced_tokens = []
        for token in tokens:
            enhanced_token = {
                **token,
                # 优先使用OKX API返回的tokenLogoUrl，如果没有则使用我们的映射
                "logoUrl": token.get("tokenLogoUrl") or get_token_logo_url(token.get("tokenSymbol", ""), token.get("tokenAddress", "")),
                # 添加代币类型
                "tokenType": get_token_type(token.get("tokenAddress", "")),
                # 添加是否为热门代币标识
                "isPopular": is_popular_token(token.get("tokenSymbol", "")),
                # 添加链ID
                "chainId": chain_id
            }
            enhanced_tokens.append(enhanced_token)
        
        # 如果有搜索关键词，进行过滤
        if search:
            search_lower = search.lower()
            enhanced_tokens = [
                token for token in enhanced_tokens
                if search_lower in token.get("tokenSymbol", "").lower() or
                   search_lower in token.get("tokenName", "").lower()
            ]
        
        # 按热门程度和符号排序
        enhanced_tokens.sort(key=lambda x: (not x.get("isPopular", False), x.get("tokenSymbol", "")))
        
        # 应用数量限制
        if limit:
            enhanced_tokens = enhanced_tokens[:limit]
            
        print(f"✅ 链 {chain_id} 最终返回 {len(enhanced_tokens)} 个代币")
        return enhanced_tokens
        
    except APIError as e:
        print(f"❌ 链 {chain_id} API错误: {str(e)}")
        # 对于某些链可能不支持，返回空列表而不是抛出错误
        if "chainId error" in str(e) or "Parameter chainId error" in str(e):
            print(f"⚠️ 链 {chain_id} 不被OKX聚合器API支持，返回空列表")
            return []
        raise HTTPException(status_code=400, detail=f"获取代币列表失败: {str(e)}")
    except Exception as e:
        print(f"❌ 链 {chain_id} 服务器错误: {str(e)}")
        # 对于未知错误，也返回空列表，避免阻塞整个应用
        return []

@router.get("/{chain_id}/{token_address}", summary="获取特定代币的详细信息")
async def get_token_info(
    chain_id: str,
    token_address: str,
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
) -> Dict[str, Any]:
    """
    获取特定代币的详细信息
    
    参数:
    - chain_id: 链ID
    - token_address: 代币合约地址
    """
    try:
        # 获取该链上的所有代币
        tokens = asset_explorer.get_token_list(chain_index=chain_id)
        
        # 查找指定地址的代币
        target_token = None
        for token in tokens:
            if token.get("tokenAddress", "").lower() == token_address.lower():
                target_token = token
                break
                
        if not target_token:
            raise HTTPException(
                status_code=404, 
                detail=f"在链 {chain_id} 上未找到地址为 {token_address} 的代币"
            )
        
        # 增强代币信息
        enhanced_token = {
            **target_token,
            "logoUrl": target_token.get("tokenLogoUrl") or get_token_logo_url(target_token.get("tokenSymbol", ""), token_address),
            "tokenType": get_token_type(token_address),
            "isPopular": is_popular_token(target_token.get("tokenSymbol", "")),
            "chainId": chain_id,
            # 添加更多详细信息
            "marketData": get_token_market_data(target_token.get("tokenSymbol", "")),
            "links": get_token_links(target_token.get("tokenSymbol", ""))
        }
        
        return enhanced_token
        
    except HTTPException:
        raise
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"获取代币信息失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/", summary="搜索代币")
async def search_tokens(
    query: str = Query(..., description="搜索关键词"),
    chains: Optional[str] = Query(None, description="指定链ID，多个用逗号分隔"),
    limit: Optional[int] = Query(50, description="返回结果数量限制"),
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
) -> List[Dict[str, Any]]:
    """
    跨链搜索代币
    
    参数:
    - query: 搜索关键词
    - chains: 指定搜索的链ID，用逗号分隔 (如 "1,56,137")
    - limit: 返回结果数量限制
    """
    try:
        # 确定要搜索的链
        if chains:
            chain_ids = [chain.strip() for chain in chains.split(",")]
        else:
            # 如果没有指定链，获取所有支持的链
            supported_chains = asset_explorer.get_supported_chains()
            chain_ids = [chain.get("chainId") for chain in supported_chains if chain.get("chainId")]
        
        all_tokens = []
        query_lower = query.lower()
        
        # 在每个链上搜索代币
        for chain_id in chain_ids:
            try:
                tokens = asset_explorer.get_token_list(chain_index=chain_id)
                for token in tokens:
                    # 检查是否匹配搜索条件
                    if (query_lower in token.get("tokenSymbol", "").lower() or
                        query_lower in token.get("tokenName", "").lower()):
                        
                        enhanced_token = {
                            **token,
                            "chainId": chain_id,
                            "logoUrl": token.get("tokenLogoUrl") or get_token_logo_url(token.get("tokenSymbol", ""), token.get("tokenAddress", "")),
                            "isPopular": is_popular_token(token.get("tokenSymbol", "")),
                        }
                        all_tokens.append(enhanced_token)
                        
            except Exception as e:
                # 如果某个链查询失败，继续查询其他链
                print(f"查询链 {chain_id} 时出错: {e}")
                continue
        
        # 按热门程度排序
        all_tokens.sort(key=lambda x: (not x.get("isPopular", False), x.get("tokenSymbol", "")))
        
        # 应用数量限制
        if limit:
            all_tokens = all_tokens[:limit]
            
        return all_tokens
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索代币时出错: {str(e)}")

@router.get("/cross-chain/{chain_index}")
async def get_cross_chain_tokens(
    chain_index: str,
    limit: int = Query(50, description="返回结果数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """获取指定链支持跨链的代币列表"""
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, '.env.local')
        load_dotenv(env_path)
        
        # 获取AssetExplorer实例
        asset_explorer = get_asset_explorer()
        
        # 使用跨链专用API
        tokens = asset_explorer.get_crosschain_tokens(chain_index)
        
        # 应用分页
        start = offset
        end = start + limit
        paginated_tokens = tokens[start:end]
        
        # 增强响应数据
        enhanced_tokens = []
        for token in paginated_tokens:
            enhanced_token = {
                **token,
                "logoUrl": token.get("tokenLogoUrl", f"https://assets.coingecko.com/coins/images/1/small/{token.get('tokenSymbol', '').lower()}.png"),
                "isPopular": token.get("tokenSymbol") in ["USDT", "USDC", "ETH", "BTC", "BNB", "MATIC"],
                "category": "cross-chain"
            }
            enhanced_tokens.append(enhanced_token)
        
        return {
            "success": True,
            "data": enhanced_tokens,
            "pagination": {
                "total": len(tokens),
                "limit": limit,
                "offset": offset,
                "hasMore": end < len(tokens)
            }
        }
        
    except Exception as e:
        print(f"获取跨链代币列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cross-chain-paths/{chain_index}/{token_address}")
async def get_cross_chain_paths(
    chain_index: str,
    token_address: str
):
    """获取指定代币的跨链目标链列表"""
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, '.env.local')
        load_dotenv(env_path)
        
        # 获取AssetExplorer实例
        asset_explorer = get_asset_explorer()
        
        # 获取所有支持的链
        chains = asset_explorer.get_supported_chains()
        
        # 获取该代币在所有链上的跨链支持情况
        supported_paths = []
        
        for target_chain in chains:
            if target_chain["chainIndex"] == chain_index:
                continue  # 跳过源链
                
            try:
                # 检查该代币是否在目标链上支持跨链
                target_tokens = asset_explorer.get_crosschain_tokens(target_chain["chainIndex"])
                
                # 查找匹配的代币（通过symbol匹配，因为地址可能不同）
                source_tokens = asset_explorer.get_crosschain_tokens(chain_index)
                source_token = next((t for t in source_tokens if t["tokenContractAddress"].lower() == token_address.lower()), None)
                
                if source_token:
                    # 在目标链查找相同symbol的代币
                    target_token = next((t for t in target_tokens if t["tokenSymbol"] == source_token["tokenSymbol"]), None)
                    
                    if target_token:
                        supported_paths.append({
                            "targetChain": target_chain,
                            "targetToken": target_token,
                            "isSupported": True
                        })
                        
            except Exception as e:
                print(f"检查链 {target_chain['chainIndex']} 跨链支持时出错: {str(e)}")
                continue
        
        return {
            "success": True,
            "data": {
                "sourceChain": chain_index,
                "sourceToken": token_address,
                "supportedPaths": supported_paths,
                "totalPaths": len(supported_paths)
            }
        }
        
    except Exception as e:
        print(f"获取跨链路径失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/route-info/{from_chain_id}/{to_chain_id}/{from_token_address}/{to_token_address}")
async def get_route_info(
    from_chain_id: str,
    to_chain_id: str,
    from_token_address: str,
    to_token_address: str,
    amount: str = Query(..., description="代币数量"),
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
):
    """
    获取跨链路径信息
    对应OKX API: /api/v5/dex/cross-chain/route
    """
    try:
        # 这里应该调用OKX的路径信息API
        # 但由于SDK中可能没有实现，我们先返回基本信息
        
        # 检查源链和目标链是否支持
        chains = asset_explorer.get_supported_chains()
        from_chain = next((c for c in chains if c["chainIndex"] == from_chain_id), None)
        to_chain = next((c for c in chains if c["chainIndex"] == to_chain_id), None)
        
        if not from_chain or not to_chain:
            raise HTTPException(status_code=400, detail="不支持的链")
        
        # 获取源链代币信息
        from_tokens = asset_explorer.get_token_list(from_chain_id)
        from_token = next((t for t in from_tokens if t["tokenContractAddress"].lower() == from_token_address.lower()), None)
        
        if not from_token:
            raise HTTPException(status_code=400, detail="源链代币不存在")
        
        # 获取目标链代币信息
        to_tokens = asset_explorer.get_token_list(to_chain_id)
        to_token = next((t for t in to_tokens if t["tokenContractAddress"].lower() == to_token_address.lower()), None)
        
        if not to_token:
            raise HTTPException(status_code=400, detail="目标链代币不存在")
        
        return {
            "success": True,
            "data": {
                "fromChain": from_chain,
                "toChain": to_chain,
                "fromToken": from_token,
                "toToken": to_token,
                "amount": amount,
                "isSupported": True,
                "routes": []  # 这里应该包含具体的路径信息
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取路径信息失败: {str(e)}")

# 辅助函数：获取代币Logo URL
def get_token_logo_url(symbol: str, address: str) -> str:
    """根据代币符号或地址返回Logo URL"""
    # 常见代币的Logo映射（使用支持CORS的图片源）
    logo_mapping = {
        "USDC": "https://assets.coingecko.com/coins/images/6319/small/USD_Coin_icon.png",
        "USDT": "https://assets.coingecko.com/coins/images/325/small/Tether.png",
        "ETH": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
        "WETH": "https://assets.coingecko.com/coins/images/2518/small/weth.png",
        "BTC": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png",
        "WBTC": "https://assets.coingecko.com/coins/images/7598/small/wrapped_bitcoin_wbtc.png",
        "BNB": "https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png",
        "MATIC": "https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png",
        "AVAX": "https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png",
        "FTM": "https://assets.coingecko.com/coins/images/4001/small/Fantom_round.png",
        "DAI": "https://assets.coingecko.com/coins/images/9956/small/Badge_Dai.png",
        "LINK": "https://assets.coingecko.com/coins/images/877/small/chainlink-new-logo.png",
        "UNI": "https://assets.coingecko.com/coins/images/12504/small/uniswap-uni.png",
        "AAVE": "https://assets.coingecko.com/coins/images/12645/small/AAVE.png",
        "COMP": "https://assets.coingecko.com/coins/images/10775/small/COMP.png",
        "SUSHI": "https://assets.coingecko.com/coins/images/12271/small/512x512_Logo_no_chop.png",
        "CRV": "https://assets.coingecko.com/coins/images/12124/small/Curve.png",
        "MKR": "https://assets.coingecko.com/coins/images/1364/small/Mark_Maker.png",
        "SNX": "https://assets.coingecko.com/coins/images/3406/small/SNX.png",
        "YFI": "https://assets.coingecko.com/coins/images/11849/small/yfi-192x192.png",
        "1INCH": "https://assets.coingecko.com/coins/images/13469/small/1inch-token.png",
        "BAL": "https://assets.coingecko.com/coins/images/11683/small/Balancer.png",
        "LDO": "https://assets.coingecko.com/coins/images/13573/small/Lido_DAO.png",
        "APE": "https://assets.coingecko.com/coins/images/18876/small/apecoin.jpg",
        "SHIB": "https://assets.coingecko.com/coins/images/11939/small/shiba.png",
        "DOGE": "https://assets.coingecko.com/coins/images/5/small/dogecoin.png",
        "ADA": "https://assets.coingecko.com/coins/images/975/small/cardano.png",
        "SOL": "https://assets.coingecko.com/coins/images/4128/small/solana.png",
        "DOT": "https://assets.coingecko.com/coins/images/12171/small/polkadot.png",
        "TRX": "https://assets.coingecko.com/coins/images/1094/small/tron-logo.png",
        "LTC": "https://assets.coingecko.com/coins/images/2/small/litecoin.png",
        "BCH": "https://assets.coingecko.com/coins/images/780/small/bitcoin-cash-circle.png",
        "XRP": "https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png",
        "ATOM": "https://assets.coingecko.com/coins/images/1481/small/cosmos_hub.png",
        "NEAR": "https://assets.coingecko.com/coins/images/10365/small/near.jpg",
        "ALGO": "https://assets.coingecko.com/coins/images/4380/small/download.png",
        "XLM": "https://assets.coingecko.com/coins/images/100/small/Stellar_symbol_black_RGB.png",
        "VET": "https://assets.coingecko.com/coins/images/1167/small/VeChain-Logo-768x725.png",
        "ICP": "https://assets.coingecko.com/coins/images/14495/small/Internet_Computer_logo.png",
        "FIL": "https://assets.coingecko.com/coins/images/12817/small/filecoin.png",
        "THETA": "https://assets.coingecko.com/coins/images/2538/small/theta-token-logo.png",
        "MANA": "https://assets.coingecko.com/coins/images/878/small/decentraland-mana.png",
        "SAND": "https://assets.coingecko.com/coins/images/12129/small/sandbox_logo.jpg",
        "AXS": "https://assets.coingecko.com/coins/images/13029/small/axie_infinity_logo.png",
        "ENJ": "https://assets.coingecko.com/coins/images/1102/small/enjin-coin-logo.png",
        "CHZ": "https://assets.coingecko.com/coins/images/8834/small/Chiliz.png",
        "FLOW": "https://assets.coingecko.com/coins/images/13446/small/5f6294c0c7a8cda55cb1c936_Flow_Wordmark.png",
        "GALA": "https://assets.coingecko.com/coins/images/12493/small/GALA-COINGECKO.png"
    }
    
    if symbol.upper() in logo_mapping:
        return logo_mapping[symbol.upper()]
    
    # 如果没有预设的Logo，使用CoinGecko的通用API
    return f"https://assets.coingecko.com/coins/images/1/small/{symbol.lower()}.png"

# 辅助函数：获取代币类型
def get_token_type(address: str) -> str:
    """根据地址判断代币类型"""
    if address == "0x0000000000000000000000000000000000000000" or not address:
        return "native"  # 原生代币
    else:
        return "erc20"   # ERC20代币

# 辅助函数：判断是否为热门代币
def is_popular_token(symbol: str) -> bool:
    """判断是否为热门代币"""
    popular_tokens = {
        "USDC", "USDT", "ETH", "BTC", "BNB", "MATIC", "AVAX", 
        "FTM", "DAI", "LINK", "UNI", "AAVE", "COMP", "SUSHI"
    }
    return symbol.upper() in popular_tokens

# 辅助函数：获取代币市场数据（模拟）
def get_token_market_data(symbol: str) -> Dict[str, Any]:
    """获取代币市场数据（这里返回模拟数据，实际可接入CoinGecko等API）"""
    return {
        "price": "0.00",
        "priceChange24h": "0.00%",
        "marketCap": "0",
        "volume24h": "0"
    }

# 辅助函数：获取代币相关链接
def get_token_links(symbol: str) -> Dict[str, str]:
    """获取代币相关链接"""
    return {
        "website": "",
        "twitter": "",
        "telegram": "",
        "discord": ""
    } 