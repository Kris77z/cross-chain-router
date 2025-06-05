"""
链信息相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import sys
import os

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
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

# 静态链信息映射（使用支持CORS的图片源）
STATIC_CHAIN_INFO = {
    "1": {
        "name": "Ethereum",
        "shortName": "ETH",
        "logoUrl": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
        "category": "Layer 1",
        "ecosystem": "Ethereum"
    },
    "56": {
        "name": "BNB Chain", 
        "shortName": "BNB",
        "logoUrl": "https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png",
        "category": "Layer 1",
        "ecosystem": "BNB Chain"
    },
    "137": {
        "name": "Polygon",
        "shortName": "MATIC", 
        "logoUrl": "https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png",
        "category": "Layer 2",
        "ecosystem": "Polygon"
    },
    "10": {
        "name": "Optimism",
        "shortName": "OP",
        "logoUrl": "https://assets.coingecko.com/coins/images/25244/small/Optimism.png",
        "category": "Layer 2", 
        "ecosystem": "Optimism"
    },
    "42161": {
        "name": "Arbitrum",
        "shortName": "ARB",
        "logoUrl": "https://assets.coingecko.com/coins/images/16547/small/photo_2023-03-29_21.47.00.jpeg",
        "category": "Layer 2",
        "ecosystem": "Arbitrum"
    },
    "43114": {
        "name": "Avalanche",
        "shortName": "AVAX",
        "logoUrl": "https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png",
        "category": "Layer 1",
        "ecosystem": "Avalanche"
    },
    "8453": {
        "name": "Base",
        "shortName": "BASE",
        "logoUrl": "https://assets.coingecko.com/coins/images/7598/small/wrapped_bitcoin_wbtc.png",
        "category": "Layer 2",
        "ecosystem": "Base"
    },
    "501": {
        "name": "Solana",
        "shortName": "SOL", 
        "logoUrl": "https://assets.coingecko.com/coins/images/4128/small/solana.png",
        "category": "Layer 1",
        "ecosystem": "Solana"
    },
    "324": {
        "name": "zkSync Era",
        "shortName": "zkSync",
        "logoUrl": "https://assets.coingecko.com/coins/images/24091/small/zkSync_era.png",
        "category": "Layer 2",
        "ecosystem": "zkSync"
    },
    "59144": {
        "name": "Linea",
        "shortName": "Linea",
        "logoUrl": "https://assets.coingecko.com/coins/images/30724/small/linea.png",
        "category": "Layer 2",
        "ecosystem": "Linea"
    },
    "534352": {
        "name": "Scroll",
        "shortName": "Scroll", 
        "logoUrl": "https://assets.coingecko.com/coins/images/26998/small/scroll.png",
        "category": "Layer 2",
        "ecosystem": "Scroll"
    },
    "195": {
        "name": "TRON",
        "shortName": "TRX",
        "logoUrl": "https://assets.coingecko.com/coins/images/1094/small/tron-logo.png",
        "category": "Layer 1",
        "ecosystem": "TRON"
    },
    "637": {
        "name": "Aptos",
        "shortName": "APT",
        "logoUrl": "https://assets.coingecko.com/coins/images/26455/small/aptos_round.png",
        "category": "Layer 1", 
        "ecosystem": "Aptos"
    },
    "784": {
        "name": "SUI",
        "shortName": "SUI",
        "logoUrl": "https://assets.coingecko.com/coins/images/26375/small/sui_asset.jpeg",
        "category": "Layer 1",
        "ecosystem": "SUI"
    },
    "196": {
        "name": "X Layer",
        "shortName": "X Layer",
        "logoUrl": "https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png", # 使用Polygon logo作为占位
        "category": "Layer 2",
        "ecosystem": "X Layer"
    },
    "169": {
        "name": "Manta Pacific",
        "shortName": "Manta",
        "logoUrl": "https://assets.coingecko.com/coins/images/28286/small/manta.png",
        "category": "Layer 2",
        "ecosystem": "Manta"
    },
    "1088": {
        "name": "Metis",
        "shortName": "METIS",
        "logoUrl": "https://assets.coingecko.com/coins/images/15595/small/metis.PNG",
        "category": "Layer 2",
        "ecosystem": "Metis"
    },
    "4200": {
        "name": "Merlin",
        "shortName": "Merlin",
        "logoUrl": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiNGRjY5MDAiLz4KPHRleHQgeD0iMTYiIHk9IjIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1zaXplPSIxNCIgZm9udC13ZWlnaHQ9ImJvbGQiPk08L3RleHQ+Cjwvc3ZnPgo=",
        "category": "Layer 2",
        "ecosystem": "Merlin"
    },
    "34443": {
        "name": "Mode",
        "shortName": "Mode", 
        "logoUrl": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiMwMEZGMDAiLz4KPHRleHQgeD0iMTYiIHk9IjIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1zaXplPSIxNCIgZm9udC13ZWlnaHQ9ImJvbGQiPk08L3RleHQ+Cjwvc3ZnPgo=",
        "category": "Layer 2",
        "ecosystem": "Mode"
    },
    "33139": {
        "name": "ApeChain",
        "shortName": "APE",
        "logoUrl": "https://assets.coingecko.com/coins/images/18876/small/apecoin.jpg",
        "category": "Layer 2",
        "ecosystem": "ApeChain"
    },
    "146": {
        "name": "Sonic Mainnet",
        "shortName": "Sonic",
        "logoUrl": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiMwMDdCRkYiLz4KPHRleHQgeD0iMTYiIHk9IjIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1zaXplPSIxNCIgZm9udC13ZWlnaHQ9ImJvbGQiPlM8L3RleHQ+Cjwvc3ZnPgo=",
        "category": "Layer 1",
        "ecosystem": "Sonic"
    }
}

# 链优先级排序
CHAIN_PRIORITY = {
    "1": 1,    # Ethereum - 最高优先级
    "56": 2,   # BNB Chain
    "137": 3,  # Polygon
    "10": 4,   # Optimism
    "42161": 5, # Arbitrum
    "43114": 6, # Avalanche
    "8453": 7,  # Base
    "501": 8,   # Solana
    "324": 9,   # zkSync Era
    "59144": 10, # Linea
    "534352": 11, # Scroll
    "195": 12,  # TRON
}

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
        print("✅ 使用API Key认证配置")
        config = Config(
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase
        )
    else:
        print("⚠️ 使用默认配置（无API Key认证）")
        config = Config()
    
    return AssetExplorer(config)

@router.get("/", summary="获取支持的链列表")
async def get_chains(
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
) -> List[Dict[str, Any]]:
    """
    获取OKX DEX支持的区块链网络列表
    
    返回增强的链信息，包含静态logo、名称等
    """
    try:
        # 获取跨链API支持的链
        cross_chain_chains = asset_explorer.get_supported_chains()
        
        # 合并静态信息
        enhanced_chains = []
        for chain in cross_chain_chains:
            chain_index = chain.get('chainId') or chain.get('chainIndex')
            static_info = STATIC_CHAIN_INFO.get(chain_index, {})
            
            # 构建增强的链信息
            enhanced_chain = {
                "chainIndex": chain_index,
                "chainName": static_info.get('name', chain.get('chainName', f"Chain {chain_index}")),
                "shortName": static_info.get('shortName', chain.get('chainName', '')),
                "logoUrl": static_info.get('logoUrl'),
                "category": static_info.get('category', 'Layer 1'),
                "ecosystem": static_info.get('ecosystem', 'Unknown'),
                # 保留原始信息
                "originalChainInfo": chain,
                # 添加一些有用的元数据
                "isMainnet": True,
                "isTestnet": False,
                "priority": CHAIN_PRIORITY.get(chain_index, 999)
            }
            
            enhanced_chains.append(enhanced_chain)
        
        # 按优先级排序
        enhanced_chains.sort(key=lambda x: x.get('priority', 999))
        
        return enhanced_chains
        
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"获取链列表失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

@router.get("/{chain_id}", summary="获取特定链的详细信息")
async def get_chain_info(
    chain_id: str,
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
) -> Dict[str, Any]:
    """
    获取特定区块链的详细信息
    
    参数:
    - chain_id: 链ID或chainIndex
    """
    try:
        # 获取所有链信息
        chains = await get_chains(asset_explorer)
        
        # 查找指定的链
        target_chain = None
        for chain in chains:
            if chain.get('chainIndex') == chain_id:
                target_chain = chain
                break
                
        if not target_chain:
            raise HTTPException(
                status_code=404, 
                detail=f"未找到链ID为 {chain_id} 的区块链信息"
            )
        
        # 添加更多详细信息
        detailed_info = {
            **target_chain,
            "supportedFeatures": get_chain_features(chain_id),
            "networkInfo": get_network_info(chain_id),
            "explorerUrls": get_explorer_urls(chain_id),
            "rpcUrls": get_rpc_urls(chain_id)
        }
        
        return detailed_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取链信息失败: {str(e)}")

@router.get("/{from_chain_id}/supported-targets", summary="获取指定源链支持的跨链目标链")
async def get_supported_target_chains(
    from_chain_id: str,
    asset_explorer: AssetExplorer = Depends(get_asset_explorer)
) -> Dict[str, Any]:
    """
    获取指定源链支持跨链的目标链列表
    
    使用静态配置的常见跨链路径，避免频繁调用OKX API导致429错误
    实际支持情况以询价API结果为准
    """
    try:
        # 静态配置的常见跨链路径（基于OKX实际支持情况）
        COMMON_CROSS_CHAIN_PATHS = {
            "1": {  # Ethereum
                "targets": ["56", "137", "10", "42161", "43114", "8453", "324", "59144", "534352"],
                "popular_tokens": ["USDT", "USDC", "ETH", "WETH", "DAI", "LINK", "UNI"]
            },
            "56": {  # BNB Chain  
                "targets": ["1", "137", "10", "42161", "43114", "8453", "324", "196"],
                "popular_tokens": ["USDT", "USDC", "BNB", "WBNB", "ETH", "BTCB"]
            },
            "137": {  # Polygon
                "targets": ["1", "56", "10", "42161", "43114", "8453", "324"],
                "popular_tokens": ["USDT", "USDC", "MATIC", "WMATIC", "ETH", "WETH"]
            },
            "10": {  # Optimism
                "targets": ["1", "56", "137", "42161", "8453", "324"],
                "popular_tokens": ["USDT", "USDC", "ETH", "WETH", "OP"]
            },
            "42161": {  # Arbitrum
                "targets": ["1", "56", "137", "10", "8453", "324", "43114"],
                "popular_tokens": ["USDT", "USDC", "ETH", "WETH", "ARB"]
            },
            "43114": {  # Avalanche
                "targets": ["1", "56", "137", "10", "42161", "8453"],
                "popular_tokens": ["USDT", "USDC", "AVAX", "WAVAX", "ETH"]
            },
            "8453": {  # Base
                "targets": ["1", "56", "137", "10", "42161", "324"],
                "popular_tokens": ["USDT", "USDC", "ETH", "WETH"]
            },
            "324": {  # zkSync Era
                "targets": ["1", "56", "137", "10", "42161", "8453"],
                "popular_tokens": ["USDT", "USDC", "ETH", "WETH"]
            },
            "501": {  # Solana
                "targets": ["1", "56", "137"],
                "popular_tokens": ["USDT", "USDC", "SOL"]
            }
        }
        
        # 获取源链配置
        source_config = COMMON_CROSS_CHAIN_PATHS.get(from_chain_id)
        if not source_config:
            return {
                "success": True,
                "data": {
                    "fromChainId": from_chain_id,
                    "supportedTargetChains": [],
                    "totalTargets": 0,
                    "message": f"链 {from_chain_id} 暂无预配置的跨链路径"
                }
            }
        
        # 构建目标链信息
        supported_targets = []
        for target_chain_id in source_config["targets"]:
            static_info = STATIC_CHAIN_INFO.get(target_chain_id, {})
            
            target_info = {
                "chainIndex": target_chain_id,
                "chainName": static_info.get('name', f"Chain {target_chain_id}"),
                "shortName": static_info.get('shortName', ''),
                "logoUrl": static_info.get('logoUrl'),
                "category": static_info.get('category', 'Layer 1'),
                "supportedTokens": source_config["popular_tokens"],
                "tokenCount": len(source_config["popular_tokens"]),
                "priority": CHAIN_PRIORITY.get(target_chain_id, 999),
                "isPopular": target_chain_id in ["56", "137", "10", "42161", "43114", "8453"]
            }
            
            supported_targets.append(target_info)
        
        # 按优先级排序
        supported_targets.sort(key=lambda x: x.get('priority', 999))
        
        return {
            "success": True,
            "data": {
                "fromChainId": from_chain_id,
                "supportedTargetChains": supported_targets,
                "totalTargets": len(supported_targets),
                "sourceTokenCount": len(source_config["popular_tokens"]),
                "commonTokens": source_config["popular_tokens"],
                "note": "实际支持情况以询价API结果为准，此列表基于常见跨链路径配置"
            }
        }
        
    except Exception as e:
        print(f"获取支持的目标链失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# 辅助函数
def get_chain_features(chain_index: str) -> List[str]:
    """获取链支持的功能"""
    features = {
        "1": ["EVM", "Smart Contracts", "DeFi", "NFT"],
        "56": ["EVM", "Smart Contracts", "DeFi", "NFT", "Low Fees"],
        "137": ["EVM", "Smart Contracts", "DeFi", "NFT", "Low Fees", "Fast"],
        "10": ["EVM", "Smart Contracts", "DeFi", "NFT", "Layer 2"],
        "42161": ["EVM", "Smart Contracts", "DeFi", "NFT", "Layer 2"],
        "501": ["Smart Contracts", "DeFi", "NFT", "High Performance"],
        "195": ["Smart Contracts", "DeFi", "High TPS"]
    }
    return features.get(chain_index, ["Smart Contracts"])

def get_network_info(chain_index: str) -> Dict[str, Any]:
    """获取网络信息"""
    network_info = {
        "1": {"blockTime": "12s", "consensus": "Proof of Stake"},
        "56": {"blockTime": "3s", "consensus": "Proof of Staked Authority"},
        "137": {"blockTime": "2s", "consensus": "Proof of Stake"},
        "501": {"blockTime": "400ms", "consensus": "Proof of History + Proof of Stake"}
    }
    return network_info.get(chain_index, {"blockTime": "Unknown", "consensus": "Unknown"})

def get_explorer_urls(chain_index: str) -> List[str]:
    """获取区块浏览器URL"""
    explorers = {
        "1": ["https://etherscan.io"],
        "56": ["https://bscscan.com"],
        "137": ["https://polygonscan.com"],
        "10": ["https://optimistic.etherscan.io"],
        "42161": ["https://arbiscan.io"],
        "43114": ["https://snowtrace.io"],
        "501": ["https://explorer.solana.com"],
        "195": ["https://tronscan.org"]
    }
    return explorers.get(chain_index, [])

def get_rpc_urls(chain_index: str) -> List[str]:
    """获取RPC URL（公共端点）"""
    rpc_urls = {
        "1": ["https://eth.llamarpc.com", "https://rpc.ankr.com/eth"],
        "56": ["https://bsc-dataseed.binance.org", "https://rpc.ankr.com/bsc"],
        "137": ["https://polygon-rpc.com", "https://rpc.ankr.com/polygon"],
        "10": ["https://mainnet.optimism.io", "https://rpc.ankr.com/optimism"],
        "42161": ["https://arb1.arbitrum.io/rpc", "https://rpc.ankr.com/arbitrum"]
    }
    return rpc_urls.get(chain_index, []) 