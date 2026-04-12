# 商城接口文档 (Mall API)

> 基于 FastAPI 自动生成的 Swagger 文档请访问 `/docs`

## 商品接口 (Products)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/products` | 获取商品列表（支持 category 过滤） | 否 |
| GET | `/products/{product_id}` | 获取单个商品详情 | 否 |

### 请求示例

```bash
# 获取商品列表
curl http://127.0.0.1:8011/products

# 获取商品详情
curl http://127.0.0.1:8011/products/1
```

### 响应示例 (GET /products)

```json
[{
  "id": 1,
  "name": "Claude API 100次",
  "slug": "claude-api-100",
  "category": "API Credits",
  "tag": null,
  "price_cny": 1.0,
  "stock": 999,
  "delivery_type": "auto",
  "is_active": true,
  "sort_order": 1
}]
```

---

## 购物车接口 (Cart)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/cart` | 获取当前用户购物车 | Bearer Token |
| POST | `/cart/items` | 添加商品到购物车 | Bearer Token |
| PATCH | `/cart/items/{item_id}` | 更新购物车商品数量 | Bearer Token |
| DELETE | `/cart/items/{item_id}` | 删除购物车商品 | Bearer Token |
| PATCH | `/cart/coupon` | 设置优惠券码 | Bearer Token |

### 请求示例

```bash
TOKEN="your_jwt_token"

# 获取购物车
curl http://127.0.0.1:8011/cart -H "Authorization: Bearer $TOKEN"

# 添加商品到购物车
curl -X POST http://127.0.0.1:8011/cart/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# 更新商品数量（quantity=0 删除）
curl -X PATCH http://127.0.0.1:8011/cart/items/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3}'

# 删除商品
curl -X DELETE http://127.0.0.1:8011/cart/items/1 \
  -H "Authorization: Bearer $TOKEN"

# 设置优惠券
curl -X PATCH http://127.0.0.1:8011/cart/coupon \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"coupon_code": "SAVE10"}'
```

### 响应示例 (GET /cart)

```json
{
  "id": 1,
  "user_id": 1,
  "coupon_code": null,
  "items": [{
    "id": 1,
    "product_id": 1,
    "quantity": 2,
    "unit_price": 0.14,
    "created_at": "2026-04-09T21:43:07"
  }],
  "subtotal": 0.28,
  "total_quantity": 2,
  "created_at": "2026-04-09T21:42:31",
  "updated_at": "2026-04-09T21:42:31"
}
```

---

## 订单接口 (Orders)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/orders` | 从购物车创建订单 | Bearer Token |
| GET | `/orders` | 获取当前用户订单列表 | Bearer Token |
| GET | `/orders/{order_id}` | 获取订单详情 | Bearer Token |

### 请求示例

```bash
TOKEN="your_jwt_token"

# 创建订单（从购物车）
curl -X POST "http://127.0.0.1:8011/orders?payment_method=wechat" \
  -H "Authorization: Bearer $TOKEN"

# 获取订单列表
curl http://127.0.0.1:8011/orders -H "Authorization: Bearer $TOKEN"

# 获取订单详情
curl http://127.0.0.1:8011/orders/1 -H "Authorization: Bearer $TOKEN"
```

### 响应示例 (POST /orders)

```json
{
  "id": 1,
  "order_no": "ORD-A77FF542FA47",
  "status": "pending",
  "total_amount": 0.42,
  "payment_method": "wechat",
  "created_at": "2026-04-09T21:43:07",
  "coupon_code": null,
  "items": [{
    "id": 1,
    "product_id": 1,
    "product_name": "Product #1",
    "quantity": 3,
    "unit_price": 0.14,
    "subtotal": 0.42,
    "created_at": "2026-04-09T21:43:07"
  }],
  "updated_at": "2026-04-09T21:43:07"
}
```

---

## 通用说明

- 所有需要认证的接口通过 `Authorization: Bearer <token>` header 传递 JWT
- 登录获取 Token: `POST /auth/login`
- 订单创建后，购物车内容自动清空
- 优惠券码在订单创建后自动核销（清空）
- 金额单位均为 USD

## 订单状态 (status)

| 状态 | 说明 |
|------|------|
| `pending` | 待支付 |
| `paid` | 已支付 |
| `shipped` | 已发货 |
| `completed` | 已完成 |
| `cancelled` | 已取消 |

## 配送类型 (delivery_type)

| 类型 | 说明 |
|------|------|
| `auto` | 自动发货（API Key等虚拟商品） |
| `manual` | 人工发货 |
| `external` | 外部链接 |
