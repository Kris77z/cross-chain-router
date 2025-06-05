# OKX 跨链桥应用

基于 OKX DEX API 的跨链桥应用，提供安全、快速的跨链资产转移服务。

## 🎯 项目概述

本项目是一个完整的跨链桥解决方案，包含：
- **前端应用**：基于 Next.js 14 + React 19 的现代化Web界面
- **后端API**：基于 FastAPI 的高性能后端服务
- **SDK封装**：对 OKX DEX API 的完整Python封装

## 🚀 已完成功能

### ✅ 核心功能
- **多链支持**：支持20+主流区块链网络（以太坊、BSC、Polygon、Arbitrum、Optimism等）
- **智能路由**：基于OKX X-Routing算法的最优路径发现
- **实时询价**：获取多个桥协议的实时报价和费用对比
- **路由排序**：支持最优、最快、数量最多三种排序模式
- **费用透明**：详细的费用分解（Gas费、桥接费、总费用）
- **安全评级**：显示每个路由的安全评级和风险评估
- **交易预估**：准确的交易时间和最小接收数量预估
- **滑点保护**：可配置的滑点容忍度设置

### ✅ 用户体验
- **响应式设计**：完美适配桌面和移动设备
- **智能搜索**：支持代币名称和地址搜索
- **实时状态**：交易状态实时追踪
- **错误处理**：友好的错误提示和处理
- **加载状态**：优雅的加载动画和状态指示
- **代币图标**：自动获取和显示代币Logo

### ✅ 技术特性
- **TypeScript**：全栈TypeScript开发，类型安全
- **现代UI**：基于shadcn/ui的现代化组件库
- **API缓存**：智能的数据缓存机制，减少重复请求
- **错误恢复**：图片加载失败时的优雅降级
- **CORS支持**：完整的跨域资源共享配置
- **环境配置**：支持多环境配置管理

## 🏗️ 项目架构

```
cross-chain-router/
├── frontend/                 # Next.js 前端应用
│   ├── src/
│   │   ├── components/       # React 组件
│   │   │   ├── ui/          # shadcn/ui 基础组件
│   │   │   └── CrossChainBridge.tsx  # 主要跨链桥组件 (1190行)
│   │   ├── app/             # Next.js 应用路由
│   │   └── lib/             # 工具函数
│   ├── package.json         # 前端依赖配置
│   └── tailwind.config.js   # Tailwind CSS 配置
├── backend/                  # FastAPI 后端服务
│   ├── routers/             # API 路由模块
│   │   ├── chains.py        # 链信息 API
│   │   ├── tokens.py        # 代币信息 API
│   │   ├── quote.py         # 询价 API
│   │   ├── transaction.py   # 交易构建 API
│   │   └── status.py        # 状态追踪 API
│   ├── main.py              # FastAPI 应用入口 (137行)
│   ├── requirements.txt     # Python 依赖
│   └── env.example          # 环境变量示例
├── okx_crosschain_sdk/      # OKX SDK 封装 (完整实现)
│   ├── __init__.py          # SDK 入口和导出
│   ├── config.py            # 配置管理 (46行)
│   ├── http_client.py       # HTTP 客户端 (178行)
│   ├── asset_explorer.py    # 资产浏览器 (186行)
│   ├── quoter.py           # 询价器 (176行)
│   ├── transaction_builder.py # 交易构建器 (211行)
│   ├── status_tracker.py    # 状态追踪器 (129行)
│   ├── onchain_gateway.py   # 链上网关 (134行)
│   └── README.md           # SDK 详细文档 (685行)
└── README.md               # 项目主文档
```

## 🛠️ 技术栈

### 前端技术栈
- **框架**：Next.js 14 (App Router)
- **UI库**：React 19
- **样式**：Tailwind CSS 4.0
- **组件库**：shadcn/ui + Radix UI
- **图标**：Lucide React
- **类型**：TypeScript 5
- **构建**：Turbopack (开发模式)

### 后端技术栈
- **框架**：FastAPI 0.104.1
- **服务器**：Uvicorn (ASGI)
- **数据验证**：Pydantic 2.5
- **HTTP客户端**：Requests 2.31
- **环境管理**：python-dotenv
- **CORS**：FastAPI CORS中间件

### SDK技术栈
- **语言**：Python 3.8+
- **HTTP客户端**：Requests
- **配置管理**：环境变量 + 类配置
- **错误处理**：自定义异常类
- **模块化设计**：功能分离的模块架构

## 📋 功能详情

### 路由排序算法
1. **最优排序**：综合考虑接收数量、费用、时间的最佳平衡
2. **最快排序**：按预估交易时间排序，适合急需完成的交易
3. **数量最多排序**：按接收代币数量排序，追求最大收益

### 费用计算
- **Gas费用**：区块链网络处理交易的费用
- **桥接费用**：跨链桥协议收取的服务费用
- **总费用**：所有费用的汇总，精确到小数点后3位

## 🔧 配置说明

### 环境变量配置
创建 `backend/.env.local` 文件（可选，用于API认证）：
```env
# OKX API 配置（可选，用于高级功能）
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase

# 服务配置
API_BASE_URL=https://www.okx.com
API_TIMEOUT=30
```

### API端点说明

#### 链信息 API
- `GET /api/v1/chains/` - 获取支持的链列表
- `GET /api/v1/chains/{from_chain_id}/supported-targets` - 获取支持的目标链

#### 代币信息 API
- `GET /api/v1/tokens/{chain_id}` - 获取特定链的代币列表
- 支持参数：`limit`（数量限制）、`search`（搜索关键词）

#### 询价 API
- `POST /api/v1/quote/` - 获取跨链交易报价
- **特性**：一次请求获取所有路由，前端智能排序
- **返回数据**：包含桥logo、代币logo、费用分解、路径步骤

#### 交易构建 API
- `POST /api/v1/transaction/build` - 构建跨链交易
- `POST /api/v1/transaction/approve` - 构建授权交易

#### 状态追踪 API
- `GET /api/v1/status/{tx_hash}` - 查询交易状态

## 🎯 使用指南

### 基本使用流程
1. **选择源链和目标链**：从支持的区块链网络中选择
2. **选择代币**：选择要转移的源代币和目标代币
3. **输入金额**：指定转移数量
4. **获取报价**：系统自动获取多个路由的报价
5. **选择路由**：根据需求选择最适合的路由
6. **查看详情**：
   - 点击路径图标查看详细步骤
   - 点击费用图标查看费用分解
7. **执行交易**：确认交易参数并执行

### 高级功能
- **滑点设置**：可调整滑点容忍度（默认0.5%）
- **路由排序**：支持三种排序模式切换
- **代币搜索**：支持按名称或地址搜索代币
- **交易状态追踪**：实时查看交易进度

## 🔒 安全特性

- ✅ **滑点保护**：防止价格滑点超出预期
- ✅ **最小接收数量**：保证最低接收数量
- ✅ **安全评级**：显示每个路由的安全评级
- ✅ **交易预估**：准确的时间和费用预估
- ✅ **多重验证**：多个桥协议的路由验证
- ✅ **错误处理**：完善的错误捕获和处理机制

## 📊 项目统计

### 代码规模
- **总代码行数**：约 3000+ 行
- **前端组件**：1190 行 (CrossChainBridge.tsx)
- **后端API**：137 行 (main.py) + 路由模块
- **SDK封装**：1000+ 行 (完整的Python SDK)
- **文档**：685 行 (SDK文档) + 项目文档

### 功能覆盖
- **支持链数量**：20+ 主流区块链
- **支持桥协议**：10+ 跨链桥
- **API端点**：15+ RESTful API
- **UI组件**：基于shadcn/ui的完整组件库


## 📈 性能优化

- 🚀 **代币列表缓存**：避免重复API请求
- ⚡ **前端排序**：减少后端计算压力
- 🎯 **智能错误处理**：优雅的错误恢复机制
- 📱 **响应式图片**：自适应图片加载
- 🔄 **优雅降级**：图片加载失败时的文字显示



## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。


---

**⚠️ 免责声明**：本项目仅用于学习和开发目的。在生产环境中使用前，请确保充分测试并了解相关风险。跨链交易涉及资金风险，请谨慎操作。 
