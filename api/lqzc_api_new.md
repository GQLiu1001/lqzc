# LQZC 商城 C端 API 文档 (详细版)

## 1. 概述

本文档为 LQZC 商城 C 端（客户端）新增功能的详细接口文档。

### 1.1. 基础信息
- **服务端口**: `http://localhost:8001`
- **基础路径**: `/mall`
- **认证方式**: Header `Authorization: Bearer <token>`，Token 由后端签发并存储在 Redis（非前端自签 JWT）

### 1.2. 标准返回结构
所有接口返回统一 JSON 格式：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

---

## 2. 客户账户 (Customer)

`基础路径: /mall/customer`

### 2.1. 客户注册
- **Endpoint**: `POST /mall/customer/register`
- **描述**: C端用户注册。
- **请求体 (Request Body)**:
  ```json
  {
    "phone": "13800138001",
    "nickname": "陈晨",              // 昵称必填，未传则后端默认取手机号后4位
    "password": "password123",      // 密码
    "register_channel": "H5"        // 注册渠道: H5, MiniApp, App
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2.2. 客户登录
- **Endpoint**: `POST /mall/customer/login`
- **描述**: 仅支持密码登录。
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
      "token": "54c3b9e2-opaque-session-token", // 后端签发，Redis 持久，非前端自签 JWT
      "customer": {
        "id": 1,
        "nickname": "陈晨",
        "phone": "13800138001",
        "avatar": "https://example.com/avatar.jpg",
        "level": 2,
        "level_name": "银卡会员"       // 来源于 member_level 配置
      }
    }
  }
  ```

### 2.3. 获取个人信息
- **Endpoint**: `GET /mall/customer/profile`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "nickname": "陈晨",
      "phone": "13800138001",
      "avatar": "https://example.com/avatar.jpg",
      "email": "chen@example.com",
      "gender": 1,
      "level": 2,
      "points_balance": 3000,
      "coupon_count": 5
    }
  }
  ```

### 2.4. 修改个人信息
- **Endpoint**: `PUT /mall/customer/profile`
- **请求体**:
  ```json
  {
    "nickname": "新昵称",
    "avatar": "https://new-avatar.url",
    "email": "new@example.com",
    "gender": 1
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2.5. 重置密码
- **Endpoint**: `POST /mall/customer/reset-password`
- **描述**: 自助重置密码。
- **请求体**:
  ```json
  {
    "phone": "13800138001",
    "old_password": "oldpassword123",
    "new_password": "newpassword123"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 2.6. 忘记密码（短信验证）
- **Endpoint**: `POST /mall/customer/forgot-password`
- **描述**: 手机号 + 短信验证码重置密码，无需旧密码。
- **请求体**:
  ```json
  {
    "phone": "13800138001",
    "sms_code": "123456",
    "new_password": "newpassword123"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 3. 收货地址 (Address)

`基础路径: /mall/address`

### 3.1. 获取地址列表
- **Endpoint**: `GET /mall/address/list`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": 1,
        "receiver_name": "陈晨",
        "receiver_phone": "13800138001",
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "detail": "科技园1号创新大厦",
        "tag": "公司",
        "is_default": 1
      }
    ]
  }
  ```

### 3.2. 新增收货地址
- **Endpoint**: `POST /mall/address/add`
- **请求体**:
  ```json
  {
    "receiver_name": "张三",
    "receiver_phone": "13900000000",
    "province": "广东省",
    "city": "广州市",
    "district": "天河区",
    "detail": "珠江新城...",
    "tag": "家",
    "is_default": 0,
    "latitude": 23.123456,
    "longitude": 113.123456
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 3.3. 修改收货地址
- **Endpoint**: `PUT /mall/address/update`
- **请求体**:
  ```json
  {
    "id": 1,
    "receiver_name": "张三",
    "receiver_phone": "13900000000",
    "province": "广东省",
    "city": "广州市",
    "district": "天河区",
    "detail": "珠江新城...",
    "tag": "家",
    "is_default": 0,
    "latitude": 23.123456,
    "longitude": 113.123456
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```


### 3.4. 删除收货地址
- **Endpoint**: `DELETE /mall/address/delete/{id}`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 4. 积分系统 (Points)

`基础路径: /mall/points`
`source_type`: 1=下单赠送, 2=退款回退, 3=支付抵扣

### 4.1. 积分概览
- **Endpoint**: `GET /mall/points/overview`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "balance": 3000,       // 可用积分
      "frozen": 0,           // 冻结积分
      "total_earned": 4800,  // 累计获取
      "total_spent": 1800    // 累计消耗
    }
  }
  ```

### 4.2. 积分流水记录
- **Endpoint**: `GET /mall/points/logs`
- **请求参数**: `current` (页码), `size` (每页条数)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 20,
      "records": [
        {
          "id": 101,
          "change_amount": 500,
          "balance_after": 3500,
          "source_type": 1,       // 1=下单赠送
          "remark": "订单完成赠送",
          "create_time": "2024-07-28T10:00:00Z"
        }
      ]
    }
  }
  ```
---

## 5. 优惠券 (Coupon)

`基础路径: /mall/coupon`

### 5.1. 领券中心列表
- **Endpoint**: `GET /mall/coupon/market`
- **描述**: 获取当前可领取的优惠券模板。
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": 1,
        "title": "满299减30",
        "type": 1,              // 1=满减
        "threshold_amount": 299.00,
        "discount_amount": 30.00,
        "valid_from": "2024-07-01",
        "valid_to": "2024-07-31",
        "is_received": false    // 当前用户是否已领
      }
    ]
  }
  ```

### 5.2. 领取优惠券
- **Endpoint**: `POST /mall/coupon/receive/{templateId}`
- **描述**: 抢券接口。
- **路径参数**: `templateId` (Long, 必填)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "领取成功",
    "data": null
  }
  ```

### 5.3. 我的优惠券
- **Endpoint**: `GET /mall/coupon/my-coupons`
- **请求参数**: `status` (0=未使用, 1=已使用, 2=已过期/失效, 3=已作废)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": 1001,
        "template_id": 1,
        "title": "满299减30",
        "code": "CC30OFF",
        "status": 0,
        "expire_time": "2024-08-01T23:59:59Z"
      }
    ]
  }
  ```

---

## 6. 订单 (Order)

`基础路径: /mall/order`
`after_sales_status`: 0=待审核, 1=处理中, 2=同意, 3=拒绝, 4=用户取消

### 6.1. 订单结算预览
- **Endpoint**: `POST /mall/order/preview`
- **描述**: 在下单前计算金额，自动匹配最佳优惠券。
- **请求体**:
  ```json
  {
    "items": [
      { "item_id": 1, "amount": 10 }
    ],
    "coupon_id": null, // 可选，指定优惠券
    "use_points": false // 是否使用积分抵扣
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total_price": 2550.00,
      "delivery_fee": 0.00,
      "discount_amount": 30.00,
      "points_deduction": 0.00,
      "payable_amount": 2520.00,
      "optimal_coupon": { "id": 1001, "title": "满299减30" }
    }
  }
  ```

### 6.2. 创建订单
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
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

### 6.3. 订单列表
- **Endpoint**: `GET /mall/order/list`
- **请求参数**: `status` (可选，缺省=全部；取值 0=待支付, 1=待发货, 2=待收货, 3=已完成, 4=已取消, 5=已关闭), `current`, `size`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 5,
      "records": [
        {
          "order_no": "ORD202407280001",
          "status": 1,
          "payable_amount": 2520.00,
          "items": [
            { "model": "A8001", "picture": "...", "amount": 10 }
          ]
        }
      ]
    }
  }
  ```

### 6.4. 订单详情
- **Endpoint**: `GET /mall/order/detail/{orderNo}`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "order_no": "ORD202310270001",
      "customer_id": 1,
      "customer_phone": "13800138001",
      "order_source": 1,
      "total_price": 3450.00,
      "payable_amount": 3400.00,
      "discount_amount": 50.00,
      "dispatch_status": 3,
      "order_status": 3,
      "pay_status": 1,
      "pay_channel": 1,
      "pay_time": "2023-10-22 10:00:00",
      "delivery_fee": 50.00,
      "goods_weight": 3.60,
      "coupon_id": 1,
      "points_used": 200,
      "expected_delivery_time": null,
      "receive_time": "2023-10-25 14:30:00",
      "remark": "客户要求下午派送",
      "create_time": "2023-10-22 09:55:00",
      "address": {
        "receiver_name": "陈晨",
        "receiver_phone": "13800138001",
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "detail": "科技园1号创新大厦"
      },
      "items": [
        {
          "id": 101,
          "item_id": 1,
          "model": "A8001",
          "specification": "800x800mm",
          "selling_price": 25.50,
          "amount": 100,
          "subtotal_price": 2550.00
        },
        {
          "id": 102,
          "item_id": 2,
          "model": "B6002",
          "specification": "600x600mm",
          "selling_price": 18.00,
          "amount": 50,
          "subtotal_price": 900.00
        }
      ],
      "status_history": [
        {
          "from_status": 0,
          "to_status": 1,
          "remark": "客户完成支付",
          "create_time": "2023-10-22 10:00:00"
        },
        {
          "from_status": 1,
          "to_status": 3,
          "remark": "配送完成签收",
          "create_time": "2023-10-25 14:30:00"
        }
      ]
    }
  }
  ```


### 6.5. 取消订单
- **Endpoint**: `POST /mall/order/cancel/{orderNo}`
- **描述**: 仅限未支付或未发货订单。
- **路径参数**: `orderNo` (String, 必填)
- **请求参数**: `reason` (String, 可选，取消原因)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```


### 6.6. 确认收货
- **Endpoint**: `POST /mall/order/confirm/{orderNo}`
- **描述**: 用户确认收货，订单完成，触发积分发放。
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "points_earned": 500  // 本次确认收货获得的积分
    }
  }
  ```


## 7. 支付 (Payment)

`基础路径: /mall/pay`

### 7.1. 发起支付 (Click to Pay)
- **Endpoint**: `POST /mall/pay/create`
- **描述**: 模拟支付/直接支付接口。前端点击支付后调用，后端直接处理支付成功逻辑（或返回模拟成功页）。
- **请求体**:
  ```json
  {
    "order_no": "ORD202407280001",
    "channel": 1  // 1=微信, 2=支付宝 (仅做记录，无实际SDK调用)
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "支付成功",
    "data": null
  }
  ```


### 7.2. 查询支付状态
- **Endpoint**: `GET /mall/pay/status/{orderNo}`
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "order_no": "ORD202407280001",
      "pay_status": 1,       // 支付记录状态：0=待支付, 1=支付成功, 2=支付失败, 3=退款中, 4=已退款；订单表 pay_status 为 0未支付/1已支付/2部分退款/3已退款
      "pay_time": "2024-07-28 10:05:00",
      "transaction_no": "WX202407280001"
    }
  }
  ```

# LQZC 商城后台管理 API 文档 (Admin API)

## 1. 概述

本文档为 LQZC 商城后台管理系统新增的 C 端业务管理接口文档。
主要涵盖客户管理、优惠券配置等功能。

### 1.1. 基础信息
- **服务端口**: `http://localhost:8001`
- **基础路径**: `/admin`
- **认证方式**: Header `Authorization: Bearer <token>` (复用现有后台管理Token)

### 1.2. 权限说明
- 接口需具备 `admin` 或特定业务角色权限方可调用。

---

## 2. 客户管理 (Customer Management)

`基础路径: /admin/customer`

### 2.1. 客户列表查询
- **Endpoint**: `GET /admin/customer/list`
- **描述**: 分页查询 C 端注册用户。
- **请求参数**:
  - `current` (Int, Default: 1): 页码
  - `size` (Int, Default: 10): 每页条数
  - `keyword` (String, Optional): 搜索关键词（手机号或昵称）
  - `level` (Int, Optional): 会员等级筛选
  - `status` (Int, Optional): 状态筛选 (1正常 0停用)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 100,
      "records": [
        {
          "id": 1,
          "nickname": "陈晨",
          "phone": "13800138001",
          "avatar": "...",
          "level": 2,
          "status": 1,
          "register_channel": "H5",
          "create_time": "2024-01-01 12:00:00"
        }
      ]
    }
  }
  ```

### 2.2. 客户注册 (Admin Create)
- **Endpoint**: `POST /admin/customer/create`
- **描述**: 后台管理员手动创建新客户（用于电话/线下订单）。
- **请求体**:
  ```json
  {
    "phone": "13900000000",
    "nickname": "张三",
    "password": "password123", // 可选，不传则默认手机号后6位或固定值
    "gender": 1,
    "remark": "线下老客户录入"
  }
  ```
- **成功响应**: 
```json
  { 
    "code": 200, 
    "message": "success", 
    "data": null
  }
```

### 2.3. 客户详情

- **Endpoint**: `GET /admin/customer/detail/{id}`
- **描述**: 获取客户详细信息，包括积分余额、统计数据等。
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "base_info": { "id": 1, "nickname": "陈晨", "phone": "138..." },
      "assets": {
        "points_balance": 3000,
        "coupon_count": 5
      },
      "stats": {
        "total_orders": 12,
        "total_spent": 5600.00
      }
    }
  }
  ```

### 2.3. 更改客户状态
- **Endpoint**: `PUT /admin/customer/status/{id}`
- **描述**: 冻结或解冻客户账号。
- **请求体**:
  ```json
  {
    "status": 0,  // 0=停用, 1=正常
    "reason": "恶意刷单"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```

---

## 3. 优惠券管理 (Coupon Management)

`基础路径: /admin/coupon`

### 3.1. 创建优惠券模板
- **Endpoint**: `POST /admin/coupon/create`
- **描述**: 创建新的优惠券活动。
- **请求体**:
  ```json
  {
    "title": "双11大促满减券",
    "type": 1,              // 1=满减, 2=折扣, 3=现金
    "threshold_amount": 299.00,
    "discount_amount": 30.00,
    "discount_rate": 0.00,
    "max_discount": null,
    "total_issued": 1000,   // 发行总量
    "per_user_limit": 1,    // 每人限领
    "valid_from": "2024-11-01 00:00:00",
    "valid_to": "2024-11-11 23:59:59"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }```

### 3.2. 优惠券模板列表
- **Endpoint**: `GET /admin/coupon/list`
- **请求参数**: `current`, `size`, `status` (1启用 0停用), `title`
- **成功响应**:
```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "records": [
        {
          "id": 1,
          "title": "满299减30",
          "type": 1,
          "status": 1,
          "received_count": 500, // 已领取数量
          "used_count": 120      // 已核销数量
        }
      ]
    }
  }
```

### 3.3. 优惠券上下架
- **Endpoint**: `PUT /admin/coupon/status/{id}`
- **描述**: 停止或恢复优惠券发放。
- **请求参数**: `status` (Int，必填，0=停用 1=启用)，`id` 通过 path 传递。
- **成功响应**: 
```json
  { 
      "code": 200, 
      "message": "success", 
      "data": null 
  }
```

### 3.4. 优惠券发放记录
- **Endpoint**: `GET /admin/coupon/record/list`
- **描述**: 查询具体的领券记录。
- **请求参数**: `template_id`, `customer_phone`, `status` (0未使用 1已使用 2过期 3作废)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 20,
      "records": [
        {
          "id": 1,
          "customer_phone": "13800138001",
          "template_id": 1,
          "status": 1,
          "use_time": "2024-07-28 10:00:00"
        }
      ]
    }
  }
  ```

---

## 4. 积分管理 (Points Management)

`基础路径: /admin/points`

### 4.1. 积分流水查询
- **Endpoint**: `GET /admin/points/log/list`
- **描述**: 查询所有用户的积分变动记录，用于对账或排查。
- **请求参数**:
  - `current` (Int, 默认1), `size` (Int, 默认10)
  - `customer_phone` (String, 可选)
  - `source_type` (Int, 可选，1=下单赠送 2=退款回退 3=支付抵扣)
  - `date_range` (String, 可选，格式 `2024-07-01,2024-07-31`)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 2,
      "records": [
        {
          "customer_phone": "13800138001",
          "change_amount": 500,
          "balance_after": 3200,
          "source_type": 1,
          "order_id": 1,
          "remark": "订单完成赠送积分",
          "create_time": "2024-07-28 10:00:00"
        },
        {
          "customer_phone": "13800138001",
          "change_amount": -200,
          "balance_after": 3000,
          "source_type": 3,
          "order_id": 1,
          "remark": "支付抵扣积分",
          "create_time": "2024-07-28 09:50:00"
        }
      ]
    }
  }
  ```

### 4.2. 人工调整积分 (慎用)
- **Endpoint**: `POST /admin/points/adjust`
- **描述**: 客服手动补偿或扣除积分。
- **请求体**:
  ```json
  {
    "customer_id": 1,
    "change_amount": 100, // 正数增加，负数扣除
    "remark": "系统故障补偿"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": null
  }
  ```


---

## 5. 会员等级管理 (Member Level)

`基础路径: /admin/member-level`

### 5.1. 等级列表
- **Endpoint**: `GET /admin/member-level/list`
- **描述**: 查看等级门槛和权益。
- **请求参数**: `current` (默认1), `size` (默认10)
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 4,
      "records": [
        {
          "id": 1,
          "level": 1,
          "name": "普通会员",
          "min_points": 0,
          "max_points": 999,
          "benefits": "下单积分",
          "create_time": "2024-01-01 00:00:00"
        }
      ]
    }
  }
  ```

### 5.2. 新增/修改等级
- **Endpoint**: `POST /admin/member-level/save`
- **请求体**:
  ```json
  {
    "level": 2,
    "name": "银卡会员",
    "min_points": 1000,
    "max_points": 4999,
    "benefits": "包邮/生日券"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data":  null 
  }
  ```
