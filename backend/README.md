# OKX Cross-Chain Bridge API Backend

基于OKX DEX API的通用跨链桥后端服务，可复用于其他项目。

## 功能特性

- 🔗 **链信息查询**: 获取支持的区块链网络和详细信息
- 🪙 **代币信息**: 查询各链上的代币列表和详情
- 💱 **智能询价**: 调用OKX X-Routing算法获取最优跨链路径
- 🔨 **交易构建**: 生成授权和跨链交易的链上数据
- 📊 **状态追踪**: 实时查询跨链交易执行状态
- 🛡️ **安全可靠**: 完整的错误处理和API认证支持

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量 (可选)

```bash
cp env.example .env
# 编辑 .env 文件，填入你的OKX API密钥 (仅OnChainGateway功能需要)
```

### 3. 启动服务

```bash
python start.py
```

或者直接使用uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### 4. 访问API文档

- Swagger UI: http://localhost:3001/docs
- ReDoc: http://localhost:3001/redoc
- 健康检查: http://localhost:3001/health

## API端点

### 链信息 (`/api/v1/chains`)

- `GET /` - 获取支持的链列表
- `GET /{chain_id}` - 获取特定链的详细信息

### 代币信息 (`/api/v1/tokens`)

- `GET /{chain_id}` - 获取特定链上的代币列表
- `GET /{chain_id}/{token_address}` - 获取特定代币详情
- `GET /` - 跨链搜索代币

### 询价 (`/api/v1/quote`)

- `POST /` - 获取跨链交易报价 (核心功能)
- `GET /estimate-time` - 预估交易时间
- `GET /supported-pairs` - 获取支持的交易对

### 交易构建 (`/api/v1/transaction`)

- `POST /approve` - 获取ERC20授权交易数据
- `POST /build` - 构建跨链交易数据
- `GET /gas-estimate` - 预估Gas费用

### 状态查询 (`/api/v1/status`)

- `GET /{tx_id}` - 查询交易状态
- `GET /batch/{tx_ids}` - 批量查询交易状态
- `GET /history/{user_address}` - 查询用户交易历史

## 使用示例

### 获取报价

```bash
curl -X POST "http://localhost:3001/api/v1/quote/" \
  -H "Content-Type: application/json" \
  -d '{
    "from_chain_id": "1",
    "to_chain_id": "56",
    "from_token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "to_token_address": "0x55d398326f99059fF775485246999027B3197955",
    "amount": "1000000",
    "user_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
    "slippage": "0.5"
  }'
```

### 查询链信息

```bash
curl "http://localhost:3001/api/v1/chains/"
```

### 查询代币列表

```bash
curl "http://localhost:3001/api/v1/tokens/1?limit=10"
```

## 项目结构

```
backend/
├── main.py              # FastAPI主应用
├── start.py             # 启动脚本
├── requirements.txt     # Python依赖
├── env.example         # 环境变量示例
├── routers/            # API路由模块
│   ├── __init__.py
│   ├── chains.py       # 链信息路由
│   ├── tokens.py       # 代币信息路由
│   ├── quote.py        # 询价路由
│   ├── transaction.py  # 交易构建路由
│   └── status.py       # 状态查询路由
└── README.md           # 本文档
```

## 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `OKX_API_KEY` | OKX API密钥 | - | 否* |
| `OKX_SECRET_KEY` | OKX Secret密钥 | - | 否* |
| `OKX_PASSPHRASE` | OKX Passphrase | - | 否* |
| `HOST` | 服务器监听地址 | `0.0.0.0` | 否 |
| `PORT` | 服务器端口 | `3001` | 否 |
| `DEBUG` | 调试模式 | `true` | 否 |

*注: API密钥仅在使用OnChainGateway功能时需要

## 错误处理

API使用标准的HTTP状态码:

- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源未找到
- `500` - 服务器内部错误

错误响应格式:
```json
{
  "error": "错误类型",
  "detail": "详细错误信息"
}
```

## 部署建议

### 生产环境

1. 使用Gunicorn或uWSGI作为WSGI服务器
2. 配置Nginx作为反向代理
3. 设置适当的环境变量
4. 启用HTTPS
5. 配置日志记录和监控

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3001

CMD ["python", "start.py"]
```

## 扩展性

这个后端服务设计为通用的跨链桥API，可以轻松扩展:

1. **添加新的路由**: 在`routers/`目录下创建新的路由文件
2. **集成其他SDK**: 修改依赖注入函数来支持其他跨链协议
3. **数据库集成**: 添加数据库支持来存储交易历史
4. **缓存优化**: 添加Redis缓存来提高性能
5. **监控告警**: 集成Prometheus/Grafana进行监控

## 许可证

本项目基于MIT许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 当前API状态 (2024年1月)

### ✅ 已验证可用的API端点

#### 1. 链信息API (`/api/v1/chains`)
- **状态**: 完全正常 ✅
- **功能**: 获取OKX DEX支持的21条区块链网络
- **测试**: 
  ```bash
  curl "http://localhost:3001/api/v1/chains/"
  curl "http://localhost:3001/api/v1/chains/1"  # 以太坊详情
  ```
- **返回数据**: 链ID、名称、Logo、原生货币、浏览器链接等

#### 2. 代币信息API (`/api/v1/tokens`)
- **状态**: 完全正常 ✅
- **功能**: 查询各链代币、跨链搜索
- **测试**:
  ```bash
  curl "http://localhost:3001/api/v1/tokens/?query=USDT"     # 搜索USDT
  curl "http://localhost:3001/api/v1/tokens/1?limit=5"      # 以太坊代币
  ```
- **返回数据**: 代币符号、名称、地址、精度、Logo等

#### 3. 询价API (`/api/v1/quote`) 
- **状态**: 待实现 🚧
- **功能**: 跨链交易报价、路径优化

#### 4. 交易构建API (`/api/v1/transaction`)
- **状态**: 待实现 🚧  
- **功能**: 生成授权和跨链交易数据

#### 5. 状态查询API (`/api/v1/status`)
- **状态**: 待实现 🚧
- **功能**: 查询交易状态和历史

### 🔧 修复记录

#### 问题1: API认证失败 (401错误)
**原因**: OKX DEX API需要API Key认证
**解决方案**: 
1. 配置`.env.local`文件存储API密钥
2. 修复所有路由的环境变量加载
3. 更新SDK的认证逻辑

#### 问题2: API端点错误 (404错误)
**原因**: 使用了错误的OKX API端点路径
**解决方案**: 
- 更正为 `/api/v5/dex/cross-chain/supported/chain`
- 使用聚合器API `/api/v5/dex/aggregator/all-tokens`

#### 问题3: 参数名称不匹配
**原因**: API参数应使用`chainIndex`而非`chainId`
**解决方案**: 统一参数命名规范

### ⚠️ 已知限制

#### API频率限制
- 部分链查询遇到429错误 (Too Many Requests)
- 建议实现请求频率控制和缓存机制

#### 不支持的链
- 某些链ID在聚合器API中不被支持 (如Aptos: 637, Mode: 34443)
- 返回"Parameter chainId error"错误

### 📊 支持的区块链网络 (21条)

| 链名称 | Chain ID | 状态 | 备注 |
|--------|----------|------|------|
| Ethereum | 1 | ✅ | 主网 |
| Polygon | 137 | ✅ | 主网 |
| BNB Chain | 56 | ✅ | 主网 |
| Arbitrum | 42161 | ✅ | L2 |
| Optimism | 10 | ✅ | L2 |
| Avalanche C | 43114 | ✅ | 主网 |
| TRON | 195 | ⚠️ | 频率限制 |
| Solana | 501 | ✅ | 主网 |
| zkSync Era | 324 | ✅ | L2 |
| Base | 8453 | ✅ | L2 |
| Linea | 59144 | ✅ | L2 |
| Scroll | 534352 | ✅ | L2 |
| 其他链 | ... | ✅/⚠️ | 详见完整列表 |

### 🚀 下一步开发

#### 优先级1: 核心功能
1. **询价API** - 实现跨链交易报价
2. **交易构建API** - 生成链上交易数据
3. **状态查询API** - 交易状态追踪

#### 优先级2: 性能优化
1. **缓存机制** - 减少API调用频率
2. **重试机制** - 处理429错误
3. **并发控制** - 限制同时请求数量

#### 优先级3: 功能增强
1. **批量查询** - 提高查询效率
2. **实时更新** - WebSocket支持
3. **历史记录** - 交易历史存储

### 🔐 安全配置

#### API Key配置
```bash
# .env.local 文件
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here  
OKX_PASSPHRASE=your_passphrase_here
```

#### 环境变量验证
- ✅ 支持`.env.local`和`.env`文件
- ✅ 自动检测API Key配置状态
- ✅ 安全的签名算法实现

### 📈 性能指标

#### 响应时间 (本地测试)
- 链信息查询: ~200ms
- 代币列表查询: ~100-500ms
- 跨链代币搜索: ~500ms-2s (取决于链数量)

#### 成功率
- 链信息API: 100% ✅
- 主流链代币API: 95%+ ✅
- 小众链代币API: 70-80% (受频率限制影响)

---

*最后更新: 2024年1月 - 基础API功能修复完成，核心功能开发中* 