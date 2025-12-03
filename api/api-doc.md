# **LQZC 瓷砖商城一体化管理平台 API 文档**

## **1. 概述**

本文档旨在为前后端开发人员提供统一、详尽的接口规范和参考。

### **1.1. 基础信息**

- **服务端口及职责**:
  - `http://localhost:8001`:
    - **后台管理核心服务 (Consul)** - 负责用户、库存、订单、司机审核、销售统计、选品单处理等核心后台功能。
    - **司机与配送服务 (Delivery)** - 负责司机端登录、接单、位置上报、路线规划等配送相关功能。
    - **线上商城服务 (Mall)** - 负责客户在线浏览商品、使用购物车、提交意向单（选品单）、AI客服等功能。
    - **C端客户服务 (Customer)** - 负责客户注册登录、收货地址、积分、优惠券、订单等功能。

### **1.2. 标准返回结构**

所有API请求成功后，将返回统一的JSON结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体的业务数据
  }
}
```

- `code`: 状态码，`200`表示成功，其他值表示不同类型的错误。
- `message`: 提示信息，成功时为`"success"`，失败时为具体的错误描述。
- `data`: 核心响应数据，可以是对象、数组或`null`。

### **1.3. 通用约定**

- **数据格式**: 前后端交互统一使用 JSON 格式。
- **命名约定**: 前端请求和后端响应的 JSON 字段均采用 **蛇形命名法 (snake_case)**。
- **金额单位**: 所有与价格、费用相关的字段（如 `price`, `fee`）均使用 `BigDecimal` 类型，以确保精度。
- **ID 类型**: 所有实体 ID 均为 `Long` 类型。

### **1.4. 关键技术设计**

#### 1.4.1. 抢券防超发
- 采用 **Redis + Lua脚本** 实现原子性抢券操作
- Lua脚本逻辑：检查库存 → 检查用户限领 → 扣减库存 → 记录领取
- Redis Key设计：
  - `coupon:stock:{templateId}` - 库存余量
  - `coupon:user:received:{templateId}:{customerId}` - 用户已领数量

#### 1.4.2. 订单库存策略
- **下单仅占位**：创建订单时不扣减数据库库存，仅在Redis中设置占位标记
- **支付扣库存**：支付成功后使用 **MyBatis-Plus乐观锁**（@Version）扣减库存
- **超时释放**：订单超时未支付，延迟队列自动释放占位（当前简化为Redis TTL）
- 乐观锁实现：`inventory_item.version` 和 `order_info.version` 字段

#### 1.4.3. C端认证方式
- C端用户登录返回UUID Token，存储在Redis（key: `customer:token:{uuid}`）
- 有效期7天，请求时通过Header `X-Customer-Token` 传递

---

## **2. 后台管理核心服务 (Consul)**

### **2.1. 用户管理 (User Management)**

`基础路径: /user`

#### **2.1.1. 用户登录**
- **Endpoint**: `POST /user/login`
- **描述**: 用户通过用户名和密码进行登录，获取认证信息。
- **请求参数 (Form Data)**:
  - `username` (String, Required): 用户的登录名。
  - `password` (String, Required): 用户的密码。
- **成功响应 (200 OK: `UserLoginResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 101,
      "username": "admin",
      "avatar": "https://example.com/avatar.jpg",
      "phone": "13800138000",
      "role_id": 1,
      "token": "eyJhbGciOiJIUzI1NiJ9...",
      "email": "admin@example.com"
    }
  }
  ```

#### **2.1.2. 用户登出**
- **Endpoint**: `GET /user/logout`
- **描述**: 当前登录用户退出，后端会清除对应的Token。

#### **2.1.3. 用户注册**
- **Endpoint**: `POST /user/register`
- **描述**: 创建一个新的用户账户。
- **请求参数 (Form Data)**:
  - `username` (String, Required): 新用户的登录名。
  - `password` (String, Required): 新用户的密码。
  - `phone` (String, Required): 新用户的手机号码。

#### **2.1.4. 重置用户密码**
- **Endpoint**: `POST /user/reset`
- **描述**: 根据用户名和手机号验证并重置密码。
- **请求参数 (Form Data)**:
  - `username` (String, Required): 需要重置密码的用户名。
  - `phone` (String, Required): 该用户绑定的手机号。
  - `new_password` (String, Required): 设置的新密码。

#### **2.1.5. 获取用户列表**
- **Endpoint**: `GET /user/list`
- **描述**: 分页获取系统中的用户列表。
- **请求参数 (Query Parameters)**:
  - `current` (Integer, Optional, default: 1): 当前页码。
  - `size` (Integer, Optional, default: 10): 每页显示的记录数。

#### **2.1.6. 修改个人信息**
- **Endpoint**: `PUT /user/change-info`
- **描述**: 当前登录用户修改自己的个人资料。

#### **2.1.7. 删除用户**
- **Endpoint**: `DELETE /user/delete/{id}`
- **描述**: (管理员权限)根据ID删除指定用户。

---

### **2.2. 库存管理 (Inventory Management)**

`基础路径: /inventory`

#### **2.2.1. 查询库存列表**
- **Endpoint**: `GET /inventory/items-list`
- **描述**: 分页并按条件筛选查询库存商品。
- **请求参数 (Query Parameters)**:
  - `current` (Integer, Optional, default: 1): 当前页码。
  - `size` (Integer, Optional, default: 10): 每页数量。
  - `category` (String, Optional): 按商品分类筛选 (e.g., "1" for 墙砖).
  - `surface` (String, Optional): 按商品饰面筛选 (e.g., "2" for 哑光).

#### **2.2.2. 修改库存商品**
- **Endpoint**: `PUT /inventory/items-change`
- **描述**: 修改指定ID的库存商品信息。

#### **2.2.3. 删除库存商品**
- **Endpoint**: `DELETE /inventory/items-delete/{id}`
- **描述**: 删除指定ID的库存商品。

#### **2.2.4. 根据型号回填信息**
- **Endpoint**: `GET /inventory/fetch/{model}`
- **描述**: 根据商品型号查询其ID和当前库存数量。

---

### **2.3. 库存日志管理 (Log Management)**

`基础路径: /logs`

#### **2.3.1. 查询操作记录**
- **Endpoint**: `GET /logs/list`
- **描述**: 分页查询出入库、调拨及冲正记录。
- **请求参数**: `log_type` (1=入库, 2=出库, 3=调拨, 4=冲正)

#### **2.3.2. 创建入库记录**
- **Endpoint**: `POST /logs/inbound`

#### **2.3.3. 创建调拨记录**
- **Endpoint**: `POST /logs/transfer`

#### **2.3.4. 修改操作记录**
- **Endpoint**: `PUT /logs/change`

#### **2.3.5. 删除日志记录**
- **Endpoint**: `DELETE /logs/delete/{id}`

---

### **2.4. 订单管理 (Order Management)**

`基础路径: /orders`

#### **2.4.1. 创建新订单**
- **Endpoint**: `POST /orders/new`
- **描述**: 创建一个包含多个商品项的新订单，并自动扣减库存。

#### **2.4.2. 查询订单列表**
- **Endpoint**: `GET /orders/list`

#### **2.4.3. 查询订单详情**
- **Endpoint**: `GET /orders/detail/{id}`

#### **2.4.4. 修改订单主信息**
- **Endpoint**: `PUT /orders/change`

#### **2.4.5. 修改/添加/删除子订单项**
- **Endpoint**: `PUT /orders/change-sub`

#### **2.4.6. 删除主订单**
- **Endpoint**: `DELETE /orders/delete/{id}`

#### **2.4.7. 更改订单派送状态**
- **Endpoint**: `PUT /orders/change/dispatch-status/{id}/{status}`
- **描述**: 后台确认客户支付并派单。此接口会同时更新：
  - `dispatch_status`: 派送状态 (0→1)
  - `pay_status`: 支付状态 (0→1)
  - `pay_channel`: 支付渠道 (1=微信, 2=支付宝)
  - `order_status`: 订单状态 (0→1)

#### **2.4.8. 创建派送单**
- **Endpoint**: `POST /orders/dispatch`

#### **2.4.9. 获取待派送订单列表**
- **Endpoint**: `GET /orders/fetch/{status}`

#### **2.4.10. 后台确认收货**
- **Endpoint**: `POST /orders/confirm-receive/{id}`
- **描述**: 后台确认订单收货，订单状态从"待确认(3)"变为"已完成(4)"，同时为用户发放积分。
- **积分规则**: 1元 = 1积分（实付金额，去除小数点向下取整）

---

### **2.5. 选品单管理 (Selection Management)**

`基础路径: /selection`

#### **2.5.1. 分页查询选品单列表**
- **Endpoint**: `GET /selection/lists`
- **请求参数**: `status` (0=待跟进, 1=已联系, 2=已到店, 3=已失效/已转订单)

#### **2.5.2. 查询选品单详情**
- **Endpoint**: `GET /selection/lists/{id}`

#### **2.5.3. 更新选品单处理状态**
- **Endpoint**: `PUT /selection/lists/{id}/status/{status}`

#### **2.5.4. 修改选品单主信息**
- **Endpoint**: `PUT /selection/lists/{id}`

#### **2.5.5. 向选品单中添加新商品**
- **Endpoint**: `POST /selection/lists/{id}/items`

#### **2.5.6. 修改选品单中某一项商品的数量**
- **Endpoint**: `PUT /selection/lists/{listId}/items/{itemId}`

#### **2.5.7. 从选品单中删除某一项商品**
- **Endpoint**: `DELETE /selection/lists/{listId}/items/{itemId}`

#### **2.5.8. 删除选品单**
- **Endpoint**: `DELETE /selection/lists/{id}`

#### **2.5.9. 选品单转为正式订单**
- **Endpoint**: `POST /selection/lists/order/{selectionListId}`

---

### **2.6. 司机管理 (Driver Management)**

`基础路径: /manager`

#### **2.6.1. 获取司机列表**
- **Endpoint**: `GET /manager/driver-list`

#### **2.6.2. 司机管理操作**
- **同意司机资格**: `PUT /manager/driver-approval/{id}`
- **拒绝司机资格**: `PUT /manager/driver-rejection/{id}`
- **删除司机账户**: `DELETE /manager/driver-delete/{id}`
- **清零司机钱包**: `DELETE /manager/driver-reset-money/{id}`

---

### **2.7. 销售统计 (Sales Statistics)**

`基础路径: /sales`

#### **2.7.1. 获取周销量Top 5商品**
- **Endpoint**: `GET /sales/top-products`

#### **2.7.2. 获取销售趋势**
- **Endpoint**: `GET /sales/trend/{year}/{month}/{length}`

---

### **2.8. 文件上传 (File Upload)**

`基础路径: /upload`

#### **2.8.1. 上传图片**
- **Endpoint**: `POST /upload/image`
- **请求类型**: `multipart/form-data`

---

## **3. 司机与配送服务 (Delivery)**

### **3.1. 司机认证与状态 (Driver Auth & Status)**

`基础路径: /driver`

#### **3.1.1. 司机登录**
- **Endpoint**: `POST /driver/login`

#### **3.1.2. 获取司机审核状态**
- **Endpoint**: `GET /driver/audit-status/{id}`

#### **3.1.3. 司机登出**
- **Endpoint**: `GET /driver/logout`

#### **3.1.4. 更新司机工作状态**
- **Endpoint**: `POST /driver/info/change-status/{id}/{status}`
- **状态**: 0=空闲, 1=忙碌, 2=离线

#### **3.1.5. 获取钱包信息**
- **Endpoint**: `GET /driver/info/wallet/{id}`

#### **3.1.6. 更新司机位置**
- **Endpoint**: `POST /driver/info/update-location`

---

### **3.2. 司机订单管理 (Delivery Management)**

`基础路径: /delivery`

#### **3.2.1. 获取司机已接订单列表**
- **Endpoint**: `GET /delivery/list`

#### **3.2.2. 获取可抢新订单**
- **Endpoint**: `GET /delivery/fetch/{status}`

#### **3.2.3. 订单操作**
- **司机抢单**: `POST /delivery/rob/{id}/{orderNo}`
- **完成派送**: `POST /delivery/complete/{orderNo}`
- **取消派送**: `POST /delivery/cancel/{orderNo}`

---

### **3.3. 路线规划 (Route Planning)**

#### **3.3.1. 腾讯地图路线规划**
- **Endpoint**: `GET /route`
- **请求参数**: `fromLat`, `toLat`, `fromLng`, `toLng`

---

## **4. 线上商城服务 (Mall)**

### **4.1. 认证与授权 (Auth)**

`基础路径: /mall/auth`

#### **4.1.1. 获取匿名Token**
- **Endpoint**: `GET /mall/auth/anonymous-token`

---

### **4.2. 商品展示 (Items Display)**

`基础路径: /mall/items`

#### **4.2.1. 查询商品列表**
- **Endpoint**: `GET /mall/items/list`

---

### **4.3. 购物车管理 (Cart Management)**

`基础路径: /mall/cart`

#### **4.3.1. 查看购物车**
- **Endpoint**: `GET /mall/cart`

#### **4.3.2. 添加/修改购物车商品**
- **添加**: `POST /mall/cart/add`
- **修改**: `POST /mall/cart/change`

#### **4.3.3. 删除购物车商品**
- **Endpoint**: `DELETE /mall/cart/delete`

#### **4.3.4. 购物车下单(提交选品单)**
- **Endpoint**: `POST /mall/cart/order`

---

### **4.4. 智能客服 (AI Chat)**

`基础路径: /mall/ai`

#### **4.4.1. AI流式聊天**
- **Endpoint**: `GET /mall/ai/stream-chat`
- **请求参数**: `message`, `sessionId`
- **响应**: `Content-Type: text/event-stream` (Server-Sent Events)

---

## **5. C端客户服务 (Customer)**

### **5.1. 客户账户 (Customer Account)**

`基础路径: /mall/customer`

#### **5.1.1. 客户注册**
- **Endpoint**: `POST /mall/customer/register`
- **请求体**:
  ```json
  {
    "phone": "13800138001",
    "nickname": "陈晨",
    "password": "password123",
    "register_channel": "H5"
  }
  ```

#### **5.1.2. 客户登录**
- **Endpoint**: `POST /mall/customer/login`
- **请求体**:
  ```json
  {
    "phone": "13800138001",
    "password": "password123"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "token": "54c3b9e2-opaque-session-token",
      "customer": {
        "id": 1,
        "nickname": "陈晨",
        "phone": "13800138001",
        "level": 2,
        "level_name": "银卡会员"
      }
    }
  }
  ```

#### **5.1.3. 获取个人信息**
- **Endpoint**: `GET /mall/customer/profile`

#### **5.1.4. 修改个人信息**
- **Endpoint**: `PUT /mall/customer/profile`

#### **5.1.5. 重置密码**
- **Endpoint**: `POST /mall/customer/reset-password`

#### **5.1.6. 忘记密码（短信验证）**
- **Endpoint**: `POST /mall/customer/forgot-password`

#### **5.1.7. 客户登出**
- **Endpoint**: `POST /mall/customer/logout`

---

### **5.2. 收货地址 (Address)**

`基础路径: /mall/address`

#### **5.2.1. 获取地址列表**
- **Endpoint**: `GET /mall/address/list`

#### **5.2.2. 新增收货地址**
- **Endpoint**: `POST /mall/address/add`

#### **5.2.3. 修改收货地址**
- **Endpoint**: `PUT /mall/address/update`

#### **5.2.4. 删除收货地址**
- **Endpoint**: `DELETE /mall/address/delete/{id}`

---

### **5.3. 积分系统 (Points)**

`基础路径: /mall/points`
`source_type`: 1=下单赠送, 2=退款回退, 3=支付抵扣

#### **5.3.1. 积分概览**
- **Endpoint**: `GET /mall/points/overview`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "balance": 3000,
      "frozen": 0,
      "total_earned": 4800,
      "total_spent": 1800
    }
  }
  ```

#### **5.3.2. 积分流水记录**
- **Endpoint**: `GET /mall/points/logs`
- **请求参数**: `current`, `size`

---

### **5.4. 优惠券 (Coupon)**

`基础路径: /mall/coupon`

#### **5.4.1. 领券中心列表**
- **Endpoint**: `GET /mall/coupon/market`
- **描述**: 获取当前可领取的优惠券模板。

#### **5.4.2. 领取优惠券**
- **Endpoint**: `POST /mall/coupon/receive/{templateId}`
- **描述**: 抢券接口，使用Redis+Lua防超发。
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "领取成功",
    "data": null
  }
  ```

#### **5.4.3. 我的优惠券**
- **Endpoint**: `GET /mall/coupon/my-coupons`
- **请求参数**: `status` (0=未使用, 1=已使用, 2=已过期/失效, 3=已作废)

---

### **5.5. C端订单 (Order)**

`基础路径: /mall/order`
`after_sales_status`: 0=待审核, 1=处理中, 2=同意, 3=拒绝, 4=用户取消

#### **5.5.1. 订单结算预览**
- **Endpoint**: `POST /mall/order/preview`
- **描述**: 在下单前计算金额，自动匹配最佳优惠券。
- **请求体**:
  ```json
  {
    "items": [
      { "item_id": 1, "amount": 10 }
    ],
    "coupon_id": null,
    "use_points": false
  }
  ```

#### **5.5.2. 创建订单**
- **Endpoint**: `POST /mall/order/create`
- **请求体**:
  ```json
  {
    "address_id": 1,
    "coupon_id": 1001,
    "points_used": 0,
    "remark": "请尽快发货",
    "items": [
      { "item_id": 1, "amount": 10 }
    ]
  }
  ```

#### **5.5.3. 订单列表**
- **Endpoint**: `GET /mall/order/list`
- **请求参数**: `status` (0=待支付, 1=待发货, 2=配送中, 3=待确认, 4=已完成, 5=已取消)

#### **5.5.4. 订单详情**
- **Endpoint**: `GET /mall/order/detail/{orderNo}`

#### **5.5.5. 取消订单**
- **Endpoint**: `POST /mall/order/cancel/{orderNo}`
- **描述**: 仅限未支付或未发货订单。

#### **5.5.6. 确认收货**
- **Endpoint**: `POST /mall/order/confirm/{orderNo}`
- **描述**: 用户确认收货，订单状态变为"已完成(4)"，触发积分发放。
- **积分计算规则**: 1元 = 1积分（实付金额，向下取整）

---

### **5.6. 支付 (Payment)**

`基础路径: /mall/pay`

#### **5.6.1. 发起支付 (Click to Pay)**
- **Endpoint**: `POST /mall/pay/create`
- **描述**: 模拟支付/直接支付接口。
- **请求体**:
  ```json
  {
    "order_no": "ORD202407280001",
    "channel": 1
  }
  ```

#### **5.6.2. 查询支付状态**
- **Endpoint**: `GET /mall/pay/status/{orderNo}`

---

## **6. 后台管理 - C端业务 (Admin API)**

### **6.1. 客户管理 (Customer Management)**

`基础路径: /admin/customer`

#### **6.1.1. 客户列表查询**
- **Endpoint**: `GET /admin/customer/list`
- **请求参数**: `keyword`, `level`, `status`

#### **6.1.2. 客户注册 (Admin Create)**
- **Endpoint**: `POST /admin/customer/create`

#### **6.1.3. 客户详情**
- **Endpoint**: `GET /admin/customer/detail/{id}`

#### **6.1.4. 更改客户状态**
- **Endpoint**: `PUT /admin/customer/status/{id}`
- **描述**: 冻结或解冻客户账号。

#### **6.1.5. 客户地址管理**
- 获取列表: `GET /admin/customer/address/list`
- 添加地址: `POST /admin/customer/address/add`
- 更新地址: `PUT /admin/customer/address/update`
- 删除地址: `DELETE /admin/customer/address/delete/{id}`

---

### **6.2. 优惠券管理 (Coupon Management)**

`基础路径: /admin/coupon`

#### **6.2.1. 创建优惠券模板**
- **Endpoint**: `POST /admin/coupon/create`
- **请求体**:
  ```json
  {
    "title": "双11大促满减券",
    "type": 1,
    "threshold_amount": 299.00,
    "discount_amount": 30.00,
    "discount_rate": 0.90,
    "max_discount": 150.00,
    "total_issued": 1000,
    "per_user_limit": 1,
    "valid_from": "2024-11-01 00:00:00",
    "valid_to": "2024-11-11 23:59:59"
  }
  ```
- **类型说明**: 1=满减, 2=折扣, 3=现金券
- **折扣券计算**: `discount_rate` 存储小数形式（0.90表示9折）

#### **6.2.2. 优惠券模板列表**
- **Endpoint**: `GET /admin/coupon/list`

#### **6.2.3. 优惠券上下架**
- **Endpoint**: `PUT /admin/coupon/status/{id}`

#### **6.2.4. 优惠券发放记录**
- **Endpoint**: `GET /admin/coupon/record/list`

#### **6.2.5. 获取用户可用优惠券**
- **Endpoint**: `GET /admin/coupon/available`

---

### **6.3. 积分管理 (Points Management)**

`基础路径: /admin/points`

#### **6.3.1. 积分流水查询**
- **Endpoint**: `GET /admin/points/log/list`

#### **6.3.2. 人工调整积分 (慎用)**
- **Endpoint**: `POST /admin/points/adjust`

---

### **6.4. 会员等级管理 (Member Level)**

`基础路径: /admin/member-level`

#### **6.4.1. 等级列表**
- **Endpoint**: `GET /admin/member-level/list`

#### **6.4.2. 新增/修改等级**
- **Endpoint**: `POST /admin/member-level/save`

---

## **附录：订单状态流转**

### 订单状态 (order_status)
| 状态值 | 状态名称 | 说明 |
|-------|---------|------|
| 0 | 待支付 | 订单创建，等待支付确认 |
| 1 | 待发货 | 已支付，等待后台派送 |
| 2 | 配送中 | 司机已接单，正在配送 |
| 3 | 待确认 | 司机已送达，等待用户/后台确认收货 |
| 4 | 已完成 | 用户/后台确认收货，积分已发放 |
| 5 | 已取消 | 订单被取消 |

### 派送状态 (dispatch_status)
| 状态值 | 状态名称 | 说明 |
|-------|---------|------|
| 0 | 待派送 | 等待后台派单 |
| 1 | 待接单 | 已派单，等待司机抢单 |
| 2 | 派送中 | 司机已接单，正在配送 |
| 3 | 已完成 | 司机已送达 |

### 完整业务流程
```
前端下单 (order_status=0, dispatch_status=0)
    ↓
后台选品单处理
    ↓
后台点击"派送" → 选择支付方式 → 选择优惠券(可选) → 确认
    ↓
系统更新: order_status=1, pay_status=1, dispatch_status=1
    ↓
司机抢单 (dispatch_status=2, order_status=2)
    ↓
司机点击"送达" (dispatch_status=3, order_status=3)
    ↓
用户/后台点击"确认收货" (order_status=4, 发放积分)
```

### 积分计算规则
- **获取积分**: 确认收货时，按实付金额计算，1元 = 1积分（去除小数点向下取整）
- **会员等级**: 根据累计获取积分（total_earned）判定等级，非当前余额
