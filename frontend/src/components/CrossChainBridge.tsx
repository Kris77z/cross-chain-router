"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowRight, 
  Settings, 
  Search, 
  Loader2, 
  RefreshCw, 
  ArrowDown, 
  TrendingUp, 
  Clock, 
  Shield, 
  Zap,
  Info,
  AlertTriangle,
  CheckCircle,
  ArrowUpDown,
  X,
  ChevronDown
} from "lucide-react";

// 类型定义
interface Chain {
  chainIndex: string;
  chainName: string;
  shortName?: string;
  logoUrl?: string;
  category?: string;
  ecosystem?: string;
  isMainnet?: boolean;
  supportedTokens?: string[];
  tokenCount?: number;
  priority?: number;
  isPopular?: boolean;
}

interface Token {
  tokenSymbol: string;
  tokenName: string;
  tokenContractAddress: string;
  decimals: string;
  logoUrl?: string;
  isPopular?: boolean;
}

interface RouteStep {
  step: number;
  action: string;
  chainId?: string;
  token?: string;
  tokenLogo?: string;
  amount?: string;
  bridge?: string;
  description: string;
}

interface QuoteRoute {
  bridgeName: string;
  bridgeId: string;
  fromTokenAmount: string;
  toTokenAmount: string;
  estimatedAmount: string;
  minimumReceived: string;
  totalFeeUsd: string;
  gasFeeUsd: string;
  bridgeFeeUsd?: string;
  estimatedTime: string | { estimatedMinutes: number; range: string };
  priceImpact: string;
  rank: number;
  isRecommended: boolean;
  safetyRating: string | { rating: string; score: number; factors: string[] };
  exchangeRate?: string;
  routeSteps?: RouteStep[];
  bridgeLogoUrl?: string;
  routeLabel?: string;
  fromTokenLogo?: string;
  toTokenLogo?: string;
  formattedFees?: {
    totalFeeUsd: string;
    formattedFee: string;
    breakdown: {
      gasFee: {
        amount: string;
        formatted: string;
        description: string;
      };
      bridgeFee: {
        amount: string;
        formatted: string;
        description: string;
      };
    };
    hasBreakdown: boolean;
  };
}

interface QuoteResult {
  success: boolean;
  data: QuoteRoute[];
  message: string;
}

// 备用链图标映射
const FALLBACK_CHAIN_ICONS: Record<string, string> = {
  "1": "Ξ", // Ethereum
  "56": "B", // BNB Chain
  "137": "◆", // Polygon
  "10": "O", // Optimism
  "42161": "A", // Arbitrum
  "43114": "▲", // Avalanche
  "195": "T", // TRON
  "501": "S", // Solana
  "637": "A", // Aptos
  "324": "Z", // zkSync Era
  "784": "~", // SUI
  "59144": "L", // Linea
  "8453": "B", // Base
  "534352": "S", // Scroll
  "196": "X", // X Layer
  "169": "M", // Manta Pacific
  "1088": "M", // Metis
  "4200": "M", // Merlin
  "34443": "M", // Mode
  "33139": "🐵", // ApeChain
  "146": "S", // Sonic Mainnet
};

// 链的原生代币映射
const NATIVE_TOKENS: Record<string, string[]> = {
  "1": ["ETH", "WETH"],           // Ethereum
  "56": ["BNB", "WBNB"],          // BNB Chain
  "137": ["MATIC", "WMATIC"],     // Polygon
  "10": ["ETH", "WETH"],          // Optimism
  "42161": ["ETH", "WETH"],       // Arbitrum
  "43114": ["AVAX", "WAVAX"],     // Avalanche
  "8453": ["ETH", "WETH"],        // Base
  "324": ["ETH", "WETH"],         // zkSync Era
  "59144": ["ETH", "WETH"],       // Linea
  "534352": ["ETH", "WETH"],      // Scroll
};

// 热门代币列表
const POPULAR_TOKENS = ["USDT", "USDC", "ETH", "WETH", "BNB", "MATIC", "AVAX"];

export default function CrossChainBridge() {
  // 状态管理
  const [chains, setChains] = useState<Chain[]>([]);
  const [fromChain, setFromChain] = useState<string>(""); // 不设置默认值
  const [toChain, setToChain] = useState<string>(""); // 不设置默认值
  
  // 代币数据 - 使用统一的代币列表
  const [allTokens, setAllTokens] = useState<Record<string, Token[]>>({});
  const [selectedFromToken, setSelectedFromToken] = useState<Token | null>(null);
  const [selectedToToken, setSelectedToToken] = useState<Token | null>(null);
  
  // 搜索状态
  const [fromTokenSearch, setFromTokenSearch] = useState("");
  const [toTokenSearch, setToTokenSearch] = useState("");
  
  // 交易数据
  const [amount, setAmount] = useState<string>(""); // 不设置默认值
  const [slippage, setSlippage] = useState<string>("0.5");
  const [quotes, setQuotes] = useState<QuoteRoute[]>([]);
  const [sortedQuotes, setSortedQuotes] = useState<QuoteRoute[]>([]);
  const [selectedQuote, setSelectedQuote] = useState<QuoteRoute | null>(null);
  
  // 加载状态
  const [isLoadingChains, setIsLoadingChains] = useState(true);
  const [isLoadingTokens, setIsLoadingTokens] = useState(false);
  const [isLoadingQuotes, setIsLoadingQuotes] = useState(false);
  
  // 高级设置
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [sortType, setSortType] = useState<"optimal" | "fastest" | "most_tokens">("optimal");
  
  // 弹窗状态
  const [showRouteDetails, setShowRouteDetails] = useState(false);
  const [selectedRouteForDetails, setSelectedRouteForDetails] = useState<QuoteRoute | null>(null);
  const [showFeeDetails, setShowFeeDetails] = useState(false);
  const [selectedRouteForFees, setSelectedRouteForFees] = useState<QuoteRoute | null>(null);

  const API_BASE = "http://localhost:3001/api/v1";

  // 初始化：获取所有支持的链
  useEffect(() => {
    fetchChains();
  }, []);

  // 当源链改变时，获取该链的代币列表（如果还没有缓存）
  useEffect(() => {
    if (fromChain && !allTokens[fromChain]) {
      fetchTokensForChain(fromChain);
    }
  }, [fromChain]);

  // 当目标链改变时，获取该链的代币列表（如果还没有缓存）
  useEffect(() => {
    if (toChain && !allTokens[toChain]) {
      fetchTokensForChain(toChain);
    }
  }, [toChain]);

  // 只有在所有必要条件都满足时才自动获取报价
  useEffect(() => {
    if (selectedFromToken && selectedToToken && amount && parseFloat(amount) > 0 && fromChain && toChain) {
      const timer = setTimeout(() => {
        handleGetQuotes();
      }, 1000); // 延迟1秒避免频繁请求
      
      return () => clearTimeout(timer);
    } else {
      // 如果条件不满足，清空报价
      setQuotes([]);
      setSortedQuotes([]);
      setSelectedQuote(null);
    }
  }, [selectedFromToken, selectedToToken, amount, slippage, fromChain, toChain]);

  // 当排序类型改变时重新排序
  useEffect(() => {
    if (quotes.length > 0) {
      const sorted = sortQuotes(quotes, sortType);
      setSortedQuotes(sorted);
      setSelectedQuote(sorted[0]); // 选择排序后的第一个
    }
  }, [sortType, quotes]);

  const fetchChains = async () => {
    try {
      setIsLoadingChains(true);
      const response = await fetch(`${API_BASE}/chains/`);
      if (response.ok) {
        const data = await response.json();
        setChains(data);
        console.log("✅ 获取链列表成功");
      }
    } catch (error) {
      console.error("获取链列表失败:", error);
    } finally {
      setIsLoadingChains(false);
    }
  };

  const fetchTokensForChain = async (chainIndex: string) => {
    try {
      setIsLoadingTokens(true);
      
      const response = await fetch(`${API_BASE}/tokens/${chainIndex}?limit=20`);
      if (response.ok) {
        const data = await response.json();
        
        // 缓存该链的代币列表
        setAllTokens(prev => ({
          ...prev,
          [chainIndex]: data
        }));
        
        // 移除自动选择代币的逻辑，让用户主动选择
        console.log(`✅ 获取链 ${chainIndex} 代币成功，共 ${data.length} 个`);
      } else {
        // 如果是400错误，可能是链不支持，设置为空数组
        if (response.status === 400) {
          console.log(`⚠️ 链 ${chainIndex} 暂不支持代币查询`);
          setAllTokens(prev => ({
            ...prev,
            [chainIndex]: []
          }));
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      }
    } catch (error) {
      console.error(`获取链 ${chainIndex} 代币失败:`, error);
      // 设置为空数组，避免重复请求
      setAllTokens(prev => ({
        ...prev,
        [chainIndex]: []
      }));
    } finally {
      setIsLoadingTokens(false);
    }
  };

  // 获取指定链的代币列表
  const getTokensForChain = (chainIndex: string): Token[] => {
    return allTokens[chainIndex] || [];
  };

  // 获取过滤后的代币列表
  const getFilteredTokens = (chainIndex: string, searchQuery: string) => {
    const tokens = getTokensForChain(chainIndex);
    
    let filtered = tokens.filter(token =>
      token.tokenSymbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      token.tokenName.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // 优先显示原生代币和热门代币
    filtered.sort((a, b) => {
      const aIsNative = NATIVE_TOKENS[chainIndex]?.includes(a.tokenSymbol);
      const bIsNative = NATIVE_TOKENS[chainIndex]?.includes(b.tokenSymbol);
      const aIsPopular = POPULAR_TOKENS.includes(a.tokenSymbol);
      const bIsPopular = POPULAR_TOKENS.includes(b.tokenSymbol);

      if (aIsNative && !bIsNative) return -1;
      if (!aIsNative && bIsNative) return 1;
      if (aIsPopular && !bIsPopular) return -1;
      if (!aIsPopular && bIsPopular) return 1;
      return a.tokenSymbol.localeCompare(b.tokenSymbol);
    });

    return filtered;
  };

  const handleGetQuotes = async () => {
    if (!selectedFromToken || !selectedToToken || !amount || parseFloat(amount) <= 0) {
      return;
    }

    try {
      setIsLoadingQuotes(true);
      setQuotes([]);
      setSortedQuotes([]);
      setSelectedQuote(null);
      
      // 计算实际发送数量（考虑代币精度）
      const amountInWei = (parseFloat(amount) * Math.pow(10, parseInt(selectedFromToken.decimals))).toString();
      
      const response = await fetch(`${API_BASE}/quote/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from_chain_id: fromChain,
          to_chain_id: toChain,
          from_token_address: selectedFromToken.tokenContractAddress,
          to_token_address: selectedToToken.tokenContractAddress,
          amount: amountInWei,
          user_address: "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6", // 示例地址
          slippage: slippage
        }),
      });

      if (response.ok) {
        const result: QuoteResult = await response.json();
        if (result.success && result.data.length > 0) {
          setQuotes(result.data);
          // 排序会在useEffect中处理
          console.log(`✅ 获取到 ${result.data.length} 条报价`);
        } else {
          console.log("❌ 未获取到有效报价");
        }
      }
    } catch (error) {
      console.error("获取报价失败:", error);
    } finally {
      setIsLoadingQuotes(false);
    }
  };

  const getChainDisplay = (chain: Chain, size: "sm" | "md" = "md") => {
    const iconSize = size === "sm" ? "w-5 h-5" : "w-6 h-6";
    const textSize = size === "sm" ? "text-sm" : "text-base";
    
    return (
      <>
        {chain.logoUrl ? (
          <img src={chain.logoUrl} alt={chain.chainName} className={`${iconSize} rounded-full`} />
        ) : (
          <div className={`${iconSize} rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs`}>
            {FALLBACK_CHAIN_ICONS[chain.chainIndex] || chain.chainName.charAt(0)}
          </div>
        )}
        <div className="flex flex-col items-start">
          <span className={`font-medium ${textSize}`}>{chain.shortName || chain.chainName}</span>
          {size === "md" && (
            <span className="text-xs text-gray-500">{chain.chainName}</span>
          )}
        </div>
      </>
    );
  };

  const getTokenDisplay = (token: Token, size: "sm" | "md" = "md") => {
    const iconSize = size === "sm" ? "w-6 h-6" : "w-8 h-8";
    const textSize = size === "sm" ? "text-sm" : "text-base";
    
    return (
      <>
        {token.logoUrl ? (
          <img src={token.logoUrl} alt={token.tokenSymbol} className={`${iconSize} rounded-full`} />
        ) : (
          <div className={`${iconSize} rounded-full bg-gradient-to-r from-green-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs`}>
            {token.tokenSymbol.charAt(0)}
          </div>
        )}
        <div className="flex flex-col items-start">
          <span className={`font-medium ${textSize}`}>{token.tokenSymbol}</span>
          {size === "md" && (
            <span className="text-xs text-gray-500">{token.tokenName}</span>
          )}
        </div>
      </>
    );
  };

  const getChainName = (chainIndex: string) => {
    const chain = chains.find(c => c.chainIndex === chainIndex);
    return chain?.chainName || `Chain ${chainIndex}`;
  };

  const formatAmount = (amount: string, decimals: string, precision: number = 6) => {
    const value = parseFloat(amount) / Math.pow(10, parseInt(decimals));
    return value.toFixed(precision);
  };

  const calculateExchangeRate = () => {
    if (!selectedQuote || !selectedFromToken || !selectedToToken || !amount) return null;
    
    const fromAmount = parseFloat(amount);
    const toAmount = parseFloat(formatAmount(selectedQuote.toTokenAmount, selectedToToken.decimals));
    const rate = toAmount / fromAmount;
    
    return `1 ${selectedFromToken.tokenSymbol} = ${rate.toFixed(6)} ${selectedToToken.tokenSymbol}`;
  };

  const handleSwapTokens = () => {
    // 交换源链和目标链
    const tempChain = fromChain;
    setFromChain(toChain);
    setToChain(tempChain);
    
    // 交换代币
    const tempToken = selectedFromToken;
    setSelectedFromToken(selectedToToken);
    setSelectedToToken(tempToken);
    
    // 清空搜索状态
    setFromTokenSearch("");
    setToTokenSearch("");
    
    // 清空报价数据
    setQuotes([]);
    setSelectedQuote(null);
  };

  // 格式化网络费用 - 保留3位小数
  const formatFeeUsd = (feeUsd: string | number): string => {
    const fee = typeof feeUsd === 'string' ? parseFloat(feeUsd) : feeUsd;
    return fee.toFixed(3);
  };

  // 获取排序类型显示文本
  const getSortTypeText = (type: string): string => {
    switch (type) {
      case "optimal": return "最优";
      case "fastest": return "最快";
      case "most_tokens": return "数量最多";
      default: return "最优";
    }
  };

  // 前端排序函数
  const sortQuotes = (quotesToSort: QuoteRoute[], type: "optimal" | "fastest" | "most_tokens"): QuoteRoute[] => {
    const sorted = [...quotesToSort];
    
    switch (type) {
      case "fastest":
        // 按预估时间排序（时间越短越好）
        sorted.sort((a, b) => {
          const timeA = getEstimatedTimeMinutes(a);
          const timeB = getEstimatedTimeMinutes(b);
          return timeA - timeB;
        });
        break;
      case "most_tokens":
        // 按收益排序（收益越高越好）
        sorted.sort((a, b) => {
          const amountA = parseFloat(a.toTokenAmount || '0');
          const amountB = parseFloat(b.toTokenAmount || '0');
          return amountB - amountA;
        });
        break;
      default: // optimal
        // 综合排序：收益优先，费用次之
        sorted.sort((a, b) => {
          const amountA = parseFloat(a.toTokenAmount || '0');
          const amountB = parseFloat(b.toTokenAmount || '0');
          const feeA = parseFloat(a.totalFeeUsd || '0');
          const feeB = parseFloat(b.totalFeeUsd || '0');
          
          // 收益差异
          const amountDiff = amountB - amountA;
          if (Math.abs(amountDiff) > 0.01) {
            return amountDiff;
          }
          
          // 如果收益相近，比较费用
          return feeA - feeB;
        });
        break;
    }
    
    // 添加排序标签
    return sorted.map((quote, index) => ({
      ...quote,
      routeLabel: getRouteLabel(index, type),
      rank: index + 1,
      isRecommended: index === 0
    }));
  };

  // 获取预估时间（分钟）
  const getEstimatedTimeMinutes = (quote: QuoteRoute): number => {
    if (typeof quote.estimatedTime === 'object' && quote.estimatedTime.estimatedMinutes) {
      return quote.estimatedTime.estimatedMinutes;
    }
    // 从字符串中提取数字（如"5分钟20秒"）
    const timeStr = typeof quote.estimatedTime === 'string' ? quote.estimatedTime : '5分钟';
    const match = timeStr.match(/(\d+)分钟/);
    return match ? parseInt(match[1]) : 5;
  };

  // 获取路由标签
  const getRouteLabel = (index: number, type: "optimal" | "fastest" | "most_tokens"): string => {
    if (index === 0) {
      switch (type) {
        case "fastest": return "最快";
        case "most_tokens": return "数量最多";
        default: return "最优";
      }
    }
    return "";
  };

  // 显示路径详情弹窗
  const showRouteDetailsModal = (quote: QuoteRoute) => {
    setSelectedRouteForDetails(quote);
    setShowRouteDetails(true);
  };

  // 显示费用详情弹窗
  const showFeeDetailsModal = (quote: QuoteRoute) => {
    setSelectedRouteForFees(quote);
    setShowFeeDetails(true);
  };

  // 渲染代币logo
  const renderTokenLogo = (logoUrl?: string, symbol?: string, size: "sm" | "md" = "md") => {
    const sizeClass = size === "sm" ? "w-4 h-4" : "w-6 h-6";
    
    if (logoUrl) {
      return (
        <img 
          src={logoUrl} 
          alt={symbol || 'Token'} 
          className={`${sizeClass} rounded-full`}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
            e.currentTarget.nextElementSibling?.classList.remove('hidden');
          }}
        />
      );
    }
    
    return (
      <div className={`${sizeClass} rounded-full bg-gradient-to-r from-green-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs`}>
        {symbol?.charAt(0) || '?'}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">跨链桥</h1>
          <p className="text-gray-600">安全、快速的跨链资产转移</p>
        </div>

        {/* 三列布局 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
          
          {/* 第一列：源链和源代币 */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>从</span>
                <Badge variant="outline" className="text-xs">源链</Badge>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* 源链选择 */}
              <div className="space-y-3">
                <span className="text-sm font-medium text-gray-600">选择网络</span>
                <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                  {isLoadingChains ? (
                    <div className="flex justify-center py-4">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : (
                    chains.slice(0, 8).map((chain) => (
                      <Button
                        key={chain.chainIndex}
                        variant={fromChain === chain.chainIndex ? "default" : "outline"}
                        className={`h-14 p-3 flex items-center gap-3 justify-start transition-all ${
                          fromChain === chain.chainIndex 
                            ? "bg-blue-600 text-white border-blue-600 shadow-lg" 
                            : "hover:bg-gray-100 hover:shadow-md"
                        }`}
                        onClick={() => setFromChain(chain.chainIndex)}
                      >
                        {getChainDisplay(chain, "sm")}
                      </Button>
                    ))
                  )}
                </div>
              </div>

              <Separator />

              {/* 源代币选择 */}
              <div className="space-y-3">
                <span className="text-sm font-medium text-gray-600">选择代币</span>
                {!fromChain ? (
                  <div className="text-center py-6 text-gray-500">
                    <div className="mb-2">
                      <AlertTriangle className="h-6 w-6 mx-auto text-gray-300" />
                    </div>
                    <p className="text-sm">请先选择源链网络</p>
                  </div>
                ) : (
                  <>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="搜索代币..."
                        value={fromTokenSearch}
                        onChange={(e) => setFromTokenSearch(e.target.value)}
                        className="pl-10"
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                        {isLoadingTokens ? (
                          <div className="flex justify-center py-4">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </div>
                        ) : getFilteredTokens(fromChain, fromTokenSearch).length > 0 ? (
                          getFilteredTokens(fromChain, fromTokenSearch).slice(0, 6).map((token) => (
                            <Button
                              key={token.tokenContractAddress}
                              variant={selectedFromToken?.tokenContractAddress === token.tokenContractAddress ? "default" : "outline"}
                              className={`h-16 p-3 flex items-center gap-3 justify-start transition-all ${
                                selectedFromToken?.tokenContractAddress === token.tokenContractAddress
                                  ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                                  : "hover:bg-gray-100 hover:shadow-md"
                              }`}
                              onClick={() => setSelectedFromToken(token)}
                            >
                              {getTokenDisplay(token, "sm")}
                            </Button>
                          ))
                        ) : (
                          <div className="text-center py-6 text-gray-500">
                            <div className="mb-2">
                              <AlertTriangle className="h-6 w-6 mx-auto text-gray-300" />
                            </div>
                            <p className="text-sm">该链暂无可用代币</p>
                            <p className="text-xs text-gray-400 mt-1">请选择其他网络</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 第二列：目标链和目标代币 */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 justify-between">
                <div className="flex items-center gap-2">
                  <span>到</span>
                  <Badge variant="outline" className="text-xs">目标链</Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSwapTokens}
                  className="h-8 w-8 p-0"
                  title="交换源链和目标链"
                >
                  <ArrowUpDown className="h-4 w-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* 目标链选择 */}
              <div className="space-y-3">
                <span className="text-sm font-medium text-gray-600">选择网络</span>
                <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                  {isLoadingChains ? (
                    <div className="flex justify-center py-4">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : (
                    chains.slice(0, 8).map((chain) => (
                      <Button
                        key={chain.chainIndex}
                        variant={toChain === chain.chainIndex ? "default" : "outline"}
                        className={`h-14 p-3 flex items-center gap-3 justify-start transition-all ${
                          toChain === chain.chainIndex 
                            ? "bg-green-600 text-white border-green-600 shadow-lg" 
                            : "hover:bg-gray-100 hover:shadow-md"
                        }`}
                        onClick={() => setToChain(chain.chainIndex)}
                      >
                        {getChainDisplay(chain, "sm")}
                      </Button>
                    ))
                  )}
                </div>
              </div>

              <Separator />

              {/* 目标代币选择 */}
              <div className="space-y-3">
                <span className="text-sm font-medium text-gray-600">选择代币</span>
                {!toChain ? (
                  <div className="text-center py-6 text-gray-500">
                    <div className="mb-2">
                      <AlertTriangle className="h-6 w-6 mx-auto text-gray-300" />
                    </div>
                    <p className="text-sm">请先选择目标链网络</p>
                  </div>
                ) : (
                  <>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="搜索代币..."
                        value={toTokenSearch}
                        onChange={(e) => setToTokenSearch(e.target.value)}
                        className="pl-10"
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                        {isLoadingTokens ? (
                          <div className="flex justify-center py-4">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </div>
                        ) : getFilteredTokens(toChain, toTokenSearch).length > 0 ? (
                          getFilteredTokens(toChain, toTokenSearch).slice(0, 6).map((token) => (
                            <Button
                              key={token.tokenContractAddress}
                              variant={selectedToToken?.tokenContractAddress === token.tokenContractAddress ? "default" : "outline"}
                              className={`h-16 p-3 flex items-center gap-3 justify-start transition-all ${
                                selectedToToken?.tokenContractAddress === token.tokenContractAddress
                                  ? "bg-green-600 text-white border-green-600 shadow-lg"
                                  : "hover:bg-gray-100 hover:shadow-md"
                              }`}
                              onClick={() => setSelectedToToken(token)}
                            >
                              {getTokenDisplay(token, "sm")}
                            </Button>
                          ))
                        ) : (
                          <div className="text-center py-6 text-gray-500">
                            <div className="mb-2">
                              <AlertTriangle className="h-6 w-6 mx-auto text-gray-300" />
                            </div>
                            <p className="text-sm">该链暂无可用代币</p>
                            <p className="text-xs text-gray-400 mt-1">请选择其他网络</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 第三列：金额输入和报价信息 */}
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 justify-between">
                <span>交易详情</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* 金额输入 */}
              <div className="space-y-3">
                <span className="text-sm font-medium text-gray-600">输入金额</span>
                <div className="relative">
                  <Input
                    type="number"
                    placeholder="0.0"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="h-16 text-2xl font-semibold pr-20"
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    {selectedFromToken && (
                      <>
                        {selectedFromToken.logoUrl && (
                          <img src={selectedFromToken.logoUrl} alt={selectedFromToken.tokenSymbol} className="w-6 h-6 rounded-full" />
                        )}
                        <span className="font-medium text-sm">
                          {selectedFromToken.tokenSymbol}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                
                {/* 快捷金额按钮 */}
                <div className="flex gap-2">
                  {["1", "10", "100", "1000"].map((preset) => (
                    <Button
                      key={preset}
                      variant="outline"
                      size="sm"
                      onClick={() => setAmount(preset)}
                      className="flex-1"
                    >
                      {preset}
                    </Button>
                  ))}
                </div>
              </div>

              {/* 高级设置 */}
              {showAdvancedSettings && (
                <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">滑点容忍度</span>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={slippage}
                        onChange={(e) => setSlippage(e.target.value)}
                        className="w-20 h-8 text-sm"
                        step="0.1"
                        min="0.1"
                        max="50"
                      />
                      <span className="text-sm text-gray-500">%</span>
                    </div>
                  </div>
                </div>
              )}

              <Separator />

              {/* 交易信息和报价 */}
              {selectedFromToken && selectedToToken ? (
                <div className="space-y-4">
                  {/* 参考汇率 */}
                  {calculateExchangeRate() && (
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600">参考汇率</span>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{calculateExchangeRate()}</span>
                        <ArrowUpDown className="h-3 w-3 text-gray-400" />
                      </div>
                    </div>
                  )}

                  {/* 滑点设置 */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">滑点</span>
                      <Info className="h-3 w-3 text-gray-400" />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{slippage}%</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                      >
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>

                  {/* 最小获得数量 */}
                  {selectedQuote && (
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600">最小获得数量</span>
                      <span className="font-medium text-sm">
                        {formatAmount(selectedQuote.minimumReceived || selectedQuote.toTokenAmount, selectedToToken.decimals)} {selectedToToken.tokenSymbol}
                      </span>
                    </div>
                  )}

                  <Separator />

                  {/* 选择跨链桥 */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-600">选择跨链桥</span>
                        <Info className="h-3 w-3 text-gray-400" />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">
                          {sortType === "optimal" && "按收取网络费用之后的预计接收价值从高到低排序"}
                          {sortType === "fastest" && "按预估交易时间从短到长排序"}
                          {sortType === "most_tokens" && "按接收代币数量从多到少排序"}
                        </span>
                        <select
                          value={sortType}
                          onChange={(e) => setSortType(e.target.value as "optimal" | "fastest" | "most_tokens")}
                          className="text-xs border rounded px-2 py-1 bg-white"
                        >
                          <option value="optimal">最优</option>
                          <option value="fastest">最快</option>
                          <option value="most_tokens">数量最多</option>
                        </select>
                      </div>
                    </div>

                    {/* 路由列表 */}
                    {sortedQuotes.length > 0 ? (
                      <div className="space-y-3 max-h-80 overflow-y-auto">
                        {sortedQuotes.map((quote, index) => (
                          <div
                            key={index}
                            className={`p-4 border rounded-lg cursor-pointer transition-all ${
                              selectedQuote === quote
                                ? "border-blue-500 bg-blue-50"
                                : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                            }`}
                            onClick={() => setSelectedQuote(quote)}
                          >
                            {/* 桥名称和标签 */}
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                {/* 隐藏桥logo，只显示桥名称 */}
                                <span className="font-medium text-sm">{quote.bridgeName}</span>
                                {quote.routeLabel && (
                                  <Badge className={`text-xs px-2 py-0.5 ${
                                    quote.routeLabel === "最优" ? "bg-green-500" :
                                    quote.routeLabel === "最快" ? "bg-blue-500" :
                                    quote.routeLabel === "数量最多" ? "bg-purple-500" :
                                    "bg-gray-500"
                                  }`}>
                                    {quote.routeLabel}
                                  </Badge>
                                )}
                              </div>
                            </div>

                            {/* 接收数量 */}
                            <div className="text-right mb-3">
                              <div className="text-lg font-bold text-gray-900">
                                {selectedToToken && formatAmount(quote.toTokenAmount, selectedToToken.decimals)} {selectedToToken?.tokenSymbol}
                              </div>
                              <div className="text-xs text-gray-500">
                                ≈ ${formatFeeUsd(quote.totalFeeUsd || "0")} (已扣除网络费用)
                              </div>
                            </div>

                            {/* 详细信息 */}
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-1">
                                  <span className="text-gray-600">预估网络费用</span>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-4 w-4 p-0"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      showFeeDetailsModal(quote);
                                    }}
                                  >
                                    <Info className="h-3 w-3 text-gray-400" />
                                  </Button>
                                </div>
                                <span className="font-medium">${formatFeeUsd(quote.totalFeeUsd || "0")}</span>
                              </div>

                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">预估耗时</span>
                                <span className="font-medium">
                                  {typeof quote.estimatedTime === 'string' 
                                    ? quote.estimatedTime 
                                    : quote.estimatedTime?.range || "5分钟20秒"
                                  }
                                </span>
                              </div>

                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">路径</span>
                                <div className="flex items-center gap-1">
                                  {/* 使用选中的代币logo而不是API返回的logo */}
                                  {renderTokenLogo(selectedFromToken?.logoUrl, selectedFromToken?.tokenSymbol, "sm")}
                                  <ArrowRight className="h-3 w-3 text-gray-400" />
                                  {renderTokenLogo(selectedToToken?.logoUrl, selectedToToken?.tokenSymbol, "sm")}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : isLoadingQuotes ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin mr-2" />
                        <span className="text-sm text-gray-500">获取报价中...</span>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <div className="mb-2">
                          <TrendingUp className="h-8 w-8 mx-auto text-gray-300" />
                        </div>
                        <p className="text-sm">请选择代币并输入金额获取报价</p>
                      </div>
                    )}
                  </div>

                  {/* 开始交易按钮 */}
                  {selectedQuote && (
                    <Button
                      className="w-full h-12 text-lg font-semibold"
                      disabled={!selectedQuote || isLoadingQuotes}
                      onClick={() => {
                        if (selectedQuote) {
                          alert(`准备开始跨链交易：\n${amount} ${selectedFromToken?.tokenSymbol} → ${formatAmount(selectedQuote.toTokenAmount, selectedToToken.decimals)} ${selectedToToken?.tokenSymbol}\n通过 ${selectedQuote.bridgeName}`);
                        }
                      }}
                    >
                      {isLoadingQuotes ? (
                        <>
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          获取报价中...
                        </>
                      ) : (
                        <>
                          <Zap className="h-5 w-5 mr-2" />
                          开始跨链交易
                        </>
                      )}
                    </Button>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="mb-4">
                    <TrendingUp className="h-12 w-12 mx-auto text-gray-300" />
                  </div>
                  <p>请选择源代币和目标代币</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 底部信息 */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-1">
              <Shield className="h-4 w-4 text-green-500" />
              <span>安全可靠</span>
            </div>
            <div className="flex items-center gap-1">
              <Zap className="h-4 w-4 text-blue-500" />
              <span>快速执行</span>
            </div>
            <div className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4 text-purple-500" />
              <span>最优价格</span>
            </div>
          </div>
        </div>

        {/* 路径详情弹窗 */}
        {showRouteDetails && selectedRouteForDetails && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">路径详情</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRouteDetails(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="space-y-4">
                {selectedRouteForDetails.routeSteps?.map((step, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">
                      {step.step}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {step.tokenLogo && renderTokenLogo(step.tokenLogo, step.token, "sm")}
                        <span className="font-medium text-sm">{step.action}</span>
                        {step.token && (
                          <span className="text-xs text-gray-500">{step.token}</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600">{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 费用详情弹窗 */}
        {showFeeDetails && selectedRouteForFees && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">费用详情</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFeeDetails(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">总费用</span>
                  <span className="font-bold">${formatFeeUsd(selectedRouteForFees.totalFeeUsd)}</span>
                </div>
                
                {selectedRouteForFees.formattedFees?.hasBreakdown && (
                  <>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <span className="text-sm font-medium">网络Gas费用</span>
                        <p className="text-xs text-gray-500">区块链网络处理费用</p>
                      </div>
                      <span className="font-medium">${formatFeeUsd(selectedRouteForFees.gasFeeUsd || "0")}</span>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <span className="text-sm font-medium">跨链桥手续费</span>
                        <p className="text-xs text-gray-500">桥协议服务费用</p>
                      </div>
                      <span className="font-medium">${formatFeeUsd(selectedRouteForFees.bridgeFeeUsd || "0")}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 