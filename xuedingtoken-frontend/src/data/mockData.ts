// Mock Data - DemoPlatform 商城 + 主站

// ============ 主站 Mock 数据 ============

// Dashboard mock 数据
export const dashMockData = {
  balance: '$0.00',
  apiKeysCount: 0,
  todayRequests: 0,
  todayCost: '$0.0000',
  todayTokens: 0,
  totalTokens: 0,
  rpm: 0,
  tpm: 0,
  avgLatency: '0ms',
  dateRange: '4月3日 - 4月9日',
  modelDistributions: [] as { model: string; count: number }[],
  tokenTrend: [] as { date: string; tokens: number }[],
}

// Keys mock 数据
export const keysMockData = {
  endpoint: 'https://api.demo-platform.com',
  keys: [] as {
    id: number; name: string; key: string; group: string;
    usage: string; rateLimit: string; expires: string;
    status: 'active' | 'inactive'; lastUsed: string; created: string;
  }[],
  groups: ['Anthropic', 'Antigravity', 'OpenAI'],
}

// Usage mock 数据
export const usageMockData = {
  totalRequests: 0,
  totalTokens: 0,
  totalCost: '$0.0000',
  avgLatency: '0ms',
  records: [] as {
    id: number; keyName: string; model: string;
    inputTokens: number; outputTokens: number; cost: string; latency: string; time: string;
  }[],
  dateRange: '近 7 天',
  granularity: '按天',
  dateOptions: ['今天', '近 7 天', '近 30 天', '本月', '上月'],
}

// Redeem mock 数据
export const redeemMockData = {
  balance: '$0.00',
  concurrentLimit: 10,
  history: [] as { id: number; code: string; amount: string; time: string }[],
  rules: [
    '每个兑换码只能使用一次',
    '兑换码可以增加余额、并发数或试用权限',
    '余额和并发数即时更新',
  ],
}

// Profile mock 数据
export const profileMockData = {
  username: 'demo_user',
  email: 'user@example.com',
  status: 'active',
  memberSince: '2026年4月',
  balance: '$0.00',
  concurrentLimit: 10,
  twoFAEnabled: false,
  twoFAOpen: false,
}

// Client Install mock 数据
export const clientInstallMockData = {
  available: false,
  keys: [] as { id: number; name: string; group: string }[],
  deployTypes: [
    { label: 'Claude Code', command: 'export ANTHROPIC_API_KEY="your-key-here"\nexport ANTHROPIC_BASE_URL="https://api.demo-platform.com"\nclaude' },
    { label: 'OpenClaw', command: 'export OPENCLAW_API_KEY="your-key-here"\nexport OPENCLAW_BASE_URL="https://api.demo-platform.com"\nopenclaw' },
  ],
}

// ============ 商城商品数据 ============
export interface Product {
  id: number
  name: string
  category: string
  tag: string
  tagLabel: string
  price: number
  priceUnit: string
  dailyLimit?: string
  stock: number
  autoDeliver: boolean
  description?: string
  models?: string[]
}

export const products: Product[] = [
  { id: 1, name: '余额充值|体验|5美金额度', category: '余额充值', tag: '体验', tagLabel: '', price: 1, priceUnit: 'CNY', stock: 10397, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 2, name: '入门版 | 15美金额度/天 | 月卡', category: '个人月卡', tag: '体验', tagLabel: '', dailyLimit: '15美元', price: 199, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 3, name: '轻量版 | 30美金额度/天 | 月卡', category: '个人月卡', tag: '轻量', tagLabel: '', dailyLimit: '30美元', price: 339, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 4, name: '标准版 ⭐ | 50美金额度/天 | 月卡', category: '个人月卡', tag: '推荐⭐', tagLabel: '', dailyLimit: '50美元', price: 499, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 5, name: '高级版👑 | 120美金额度/天 | 月卡', category: '个人月卡', tag: '进阶👑', tagLabel: '', dailyLimit: '120美元', price: 1188, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 6, name: '团队版 | 200美金额度/天 | 月卡', category: '团队月卡', tag: '起步✈️', tagLabel: '', dailyLimit: '200美元', price: 1888, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 7, name: '商业版⭐ | 500美金额度/天 | 月卡', category: '团队月卡', tag: '推荐', tagLabel: '', dailyLimit: '500美元', price: 4688, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 8, name: '企业版 👑 | 1000美金额度/天 | 月卡', category: '团队月卡', tag: '旗舰👑', tagLabel: '', dailyLimit: '1000美元', price: 9188, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 9, name: 'AI员工|按量付费|1000算力', category: '企业服务算力专区', tag: '', tagLabel: '', price: 1000, priceUnit: 'CNY', stock: 9999, autoDeliver: true },
  { id: 10, name: 'AI员工|按量付费|5000算力', category: '企业服务算力专区', tag: '', tagLabel: '', price: 5000, priceUnit: 'CNY', stock: 9999, autoDeliver: true },
  { id: 11, name: '余额充值|50美金额度', category: '余额充值', tag: '', tagLabel: '', price: 50, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 12, name: '余额充值|20美金额度', category: '余额充值', tag: '', tagLabel: '', price: 20, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 13, name: '余额充值|500美金额度', category: '余额充值', tag: '', tagLabel: '', price: 500, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 14, name: '余额充值|100美金额度', category: '余额充值', tag: '', tagLabel: '', price: 100, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
  { id: 15, name: '余额充值|1000美金额度', category: '余额充值', tag: '', tagLabel: '', price: 1000, priceUnit: 'CNY', stock: 9999, autoDeliver: true, models: ['opus', 'sonnet', 'haiku'] },
]

export const categories = ['全部', '个人月卡', '团队月卡', '企业服务算力专区', '余额充值']

// ============ 购物车数据 ============
export interface CartItem {
  product: Product
  quantity: number
}

export const cartItems: CartItem[] = []

// ============ 主站数据 ============
export interface DashStat {
  label: string
  value: string
  sub?: string
  icon?: string
}

export const dashStats: DashStat[] = [
  { label: '余额', value: '$0.00', sub: '可用', icon: '💰' },
  { label: 'API 密钥', value: '0', sub: '0 启用', icon: '🔑' },
  { label: '今日请求', value: '0', sub: '总计: 0', icon: '📊' },
  { label: '今日消费', value: '$0.0000', sub: '总计: $0.0000', icon: '💸' },
  { label: '今日 Token', value: '0', sub: '输入: 0 / 输出: 0', icon: '🔢' },
  { label: '累计 Token', value: '0', sub: '输入: 0 / 输出: 0', icon: '📈' },
]

export const performanceStats = [
  { label: 'RPM', value: '0' },
  { label: 'TPM', value: '0' },
  { label: '平均响应', value: '0ms' },
]

export interface UsageRecord {
  id: number
  keyName: string
  model: string
  inputTokens: number
  outputTokens: number
  cost: string
  latency: string
  time: string
}

export const usageRecords: UsageRecord[] = []

export interface ApiKey {
  id: number
  name: string
  key: string
  group: string
  usage: string
  rateLimit: string
  expires: string
  status: 'active' | 'inactive'
  lastUsed: string
  created: string
}

export const apiKeys: ApiKey[] = []

export const apiGroups = ['Anthropic', 'Antigravity', 'OpenAI', '全部']

// ============ 用户数据 ============
export interface User {
  username: string
  email: string
  balance: string
  concurrentLimit: number
  memberSince: string
  status: 'active' | 'inactive'
}

export const currentUser: User = {
  username: 'demo_user',
  email: 'user@example.com',
  balance: '$0.00',
  concurrentLimit: 10,
  memberSince: '2026年4月',
  status: 'active',
}

// ============ 公告数据 ============
export interface Notice {
  id: number
  title: string
  date: string
  content?: string
}

export const notices: Notice[] = [
  { id: 1, title: '欢迎使用DemoPlatform的算力', date: '2026年3月21日' },
]

// ============ 订单数据 ============
export type OrderStatus = '待支付' | '已支付' | '处理中' | '部分交付' | '已交付' | '已完成' | '已退款' | '已过期' | '已取消'

export interface Order {
  id: string
  status: OrderStatus
  productName: string
  amount: string
  date: string
}

export const orders: Order[] = []
