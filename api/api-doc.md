# **lqzc一体化管理平台 API 文档**

## **1. 概述**

本文档旨在为前后端开发人员提供统一、详尽的接口规范和参考。

### **1.1. 基础信息**

- **服务端口及职责**:
  - `http://localhost:8001`:
    - **后台管理核心服务 (Consul)** - 负责用户、库存、订单、司机审核、销售统计、选品单处理等核心后台功能。
    - **司机与配送服务 (Delivery)** - 负责司机端登录、接单、位置上报、路线规划等配送相关功能。
    - **线上商城服务 (Mall)** - 负责客户在线浏览商品、使用购物车、提交意向单（选品单）、AI客服等功能。

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
      "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsImlkIjoxMDEsImV4cCI6MTY4OTk4ODAwMH0.abcdefg...",
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
- **成功响应 (200 OK: `UserListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 55,
      "current": 1,
      "size": 10,
      "records": [
        {
          "id": 102,
          "username": "sales_manager",
          "phone": "13912345678",
          "role_id": 2
        },
        {
          "id": 103,
          "username": "warehouse_staff",
          "phone": "13787654321",
          "role_id": 3
        }
      ]
    }
  }
  ```

#### **2.1.6. 修改个人信息**
- **Endpoint**: `PUT /user/change-info`
- **描述**: 当前登录用户修改自己的个人资料。
- **请求体 (Request Body: `UserChangeInfoReq`)**:
  ```json
  {
    "username": "new_username",
    "password": "old_password_123",
    "new_password": "new_secure_password_456",
    "phone": "13800138001",
    "avatar": "https://example.com/new_avatar.png",
    "email": "new.email@example.com"
  }
  ```

#### **2.1.7. 删除用户**
- **Endpoint**: `DELETE /user/delete/{id}`
- **描述**: (管理员权限)根据ID删除指定用户。
- **路径参数 (Path Variable)**:
  - `id` (Long, Required): 要删除的用户ID。

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
- **成功响应 (200 OK: `ItemsListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 28,
      "current": 1,
      "size": 10,
      "records": [
        {
          "id": 1,
          "model": "M-800x800-001",
          "manufacturer": "东鹏瓷砖",
          "specification": "800x800mm",
          "surface": 1,
          "category": 2,
          "warehouse_num": 1,
          "total_amount": 1200,
          "unit_per_box": 4,
          "selling_price": 45.50,
          "picture": "https://example.com/tile1.jpg",
          "remark": "高光耐磨地砖",
          "create_time": "2024-07-26T10:00:00Z",
          "update_time": "2024-07-26T10:00:00Z"
        }
      ]
    }
  }
  ```

#### **2.2.2. 修改库存商品**
- **Endpoint**: `PUT /inventory/items-change`
- **描述**: 修改指定ID的库存商品信息。
- **请求体 (Request Body: `ItemsChangeReq`)**:
  ```json
  {
    "id": 1,
    "model": "M-800x800-001-PRO",
    "manufacturer": "东鹏瓷砖",
    "specification": "800x800mm",
    "surface": 2,
    "category": 2,
    "warehouse_num": 1,
    "total_amount": 1150,
    "unit_per_box": 4,
    "selling_price": 48.00,
    "picture": "https://example.com/tile1_pro.jpg",
    "remark": "升级款哑光耐磨地砖"
  }
  ```

#### **2.2.3. 删除库存商品**
- **Endpoint**: `DELETE /inventory/items-delete/{id}`
- **描述**: 删除指定ID的库存商品。
- **路径参数 (Path Variable)**:
  - `id` (Long, Required): 要删除的商品ID。

#### **2.2.4. 根据型号回填信息**
- **Endpoint**: `GET /inventory/fetch/{model}`
- **描述**: 根据商品型号查询其ID和当前库存数量。
- **路径参数 (Path Variable)**:
  - `model` (String, Required): 商品型号。
- **成功响应 (200 OK: `IetmsFetchResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "total_amount": 1150
    }
  }
  ```

---

### **2.3. 库存日志管理 (Log Management)**

`基础路径: /logs`

#### **2.3.1. 查询操作记录**
- **Endpoint**: `GET /logs/list`
- **描述**: 分页查询出入库、调拨及冲正记录。
- **请求参数 (Query Parameters)**:
  - `current` (Integer, Optional, default: 1): 当前页码。
  - `size` (Integer, Optional, default: 10): 每页数量。
  - `log_type` (Integer, Required): 记录类型 (1=入库, 2=出库, 3=调拨, 4=冲正)。
  - `start_time` (String, Optional): 查询起始时间 (格式: `YYYY-MM-DDTHH:mm:ssZ`)。
  - `end_time` (String, Optional): 查询结束时间 (格式: `YYYY-MM-DDTHH:mm:ssZ`)。
- **成功响应 (200 OK: `LogsListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 15,
      "current": 1,
      "size": 10,
      "records": [
        {
          "id": 10,
          "item_id": 1,
          "log_type": 1,
          "amount_change": 200,
          "source_warehouse": null,
          "target_warehouse": 1,
          "remark": "新批次到货",
          "create_time": "2024-07-25T09:00:00Z",
          "update_time": "2024-07-25T09:00:00Z"
        }
      ]
    }
  }
  ```

#### **2.3.2. 创建入库记录**
- **Endpoint**: `POST /logs/inbound`
- **描述**: 创建一条新的入库记录。如果商品型号不存在，则会创建新商品。
- **请求体 (Request Body: `LogsInboundReq`)**:
  ```json
  {
    "model": "W-600x1200-003",
    "manufacturer": "马可波罗",
    "specification": "600x1200mm",
    "warehouse_num": 2,
    "category": 1,
    "surface": 3,
    "total_amount": 300,
    "unit_per_box": 2,
    "selling_price": 88.00,
    "picture": "https://example.com/tile_large.jpg",
    "remark": "项目A采购入库"
  }
  ```

#### **2.3.3. 创建调拨记录**
- **Endpoint**: `POST /logs/transfer`
- **描述**: 创建一条新的商品调拨记录。
- **请求体 (Request Body: `LogsTransferReq`)**:
  ```json
  {
    "item_id": 1,
    "log_type": 3,
    "source_warehouse": 1,
    "target_warehouse": 2,
    "remark": "调拨至2号仓库以备发货"
  }
  ```
#### **2.3.4. 修改操作记录**
- **Endpoint**: `PUT /logs/change`
- **描述**: 对现有记录进行冲正并生成新记录，以实现“修改”效果。
- **请求体 (Request Body: `LogsChangeReq`)**:
  ```json
  {
    "id": 10,
    "item_id": 1,
    "log_type": 1,
    "source_warehouse": null,
    "target_warehouse": 1,
    "amount_change": 180,
    "remark": "修正：实际到货180箱"
  }
  ```

#### **2.3.5. 删除日志记录**
- **Endpoint**: `DELETE /logs/delete/{id}`
- **描述**: (高风险操作)直接删除指定的日志记录。
- **路径参数 (Path Variable)**:
  - `id` (Long, Required): 要删除的日志ID。

---

### **2.4. 订单管理 (Order Management)**

`基础路径: /orders`

#### **2.4.1. 创建新订单**
- **Endpoint**: `POST /orders/new`
- **描述**: 创建一个包含多个商品项的新订单，并自动扣减库存。
- **请求体 (Request Body: `OrderNewReq`)**:
  ```json
  {
    "customer_phone": "13888888888",
    "total_price": 9875.00,
    "remark": "客户要求发票抬头：xxx公司",
    "items": [
      {
        "item_id": 1,
        "model": "M-800x800-001",
        "amount": 100,
        "subtotal_price": 4550.00
      },
      {
        "item_id": 2,
        "model": "W-600x1200-003",
        "amount": 60,
        "subtotal_price": 5325.00
      }
    ]
  }
  ```
#### **2.4.2. 查询订单列表**
- **Endpoint**: `GET /orders/list`
- **成功响应 (200 OK: `OrderListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 12,
      "current": 1,
      "size": 10,
      "records": [
        {
          "id": 1,
          "order_no": "ORD20240726001",
          "customer_phone": "13888888888",
          "total_price": 9875.00,
          "dispatch_status": 0,
          "remark": "客户要求发票抬头：xxx公司",
          "create_time": "2024-07-26T14:30:00Z",
          "update_time": "2024-07-26T14:30:00Z",
          "sub_order_count": 2
        }
      ]
    }
  }
  ```

#### **2.4.3. 查询订单详情**
- **Endpoint**: `GET /orders/detail/{id}`
- **成功响应 (200 OK: `OrderDetailResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "order_no": "ORD20240726001",
      "customer_phone": "13888888888",
      "total_price": 9875.00,
      "remark": "客户要求发票抬头：xxx公司",
      "create_time": "2024-07-26T14:30:00Z",
      "update_time": "2024-07-26T14:30:00Z",
      "sub_order": [
        {
          "id": 1,
          "order_id": 1,
          "item_id": 1,
          "amount": 100,
          "subtotal_price": 4550.00,
          "create_time": "2024-07-26T14:30:00Z",
          "update_time": "2024-07-26T14:30:00Z"
        }
      ]
    }
  }
  ```

#### **2.4.4. 修改订单主信息**
- **Endpoint**: `PUT /orders/change`
- **请求体 (Request Body: `OrderChangeReq`)**:
  ```json
  {
    "id": 1,
    "customer_phone": "13888888889",
    "remark": "更新备注：客户要求周六送货"
  }
  ```

#### **2.4.5. 修改/添加/删除子订单项**
- **Endpoint**: `PUT /orders/change-sub`
- **请求体 (Request Body: `OrderSubChangeReq`)**:
  - `change_type`: 0=修改, 1=添加, 2=删除
  ```json
  {
    "id": 1,
    "order_id": 1,
    "item_id": 1,
    "amount": 110,
    "subtotal_price": 5005.00,
    "change_type": 0
  }
  ```
#### **2.4.6. 删除主订单**
- **Endpoint**: `DELETE /orders/delete/{id}`
- **描述**: 删除整个订单，并将涉及的商品库存进行回滚。

#### **2.4.7. 更改订单派送状态**
- **Endpoint**: `PUT /orders/change/dispatch-status/{id}/{status}`

#### **2.4.8. 创建派送单**
- **Endpoint**: `POST /orders/dispatch`
- **描述**: 将一个订单信息转为派送任务。
- **请求体 (Request Body: `OrderDispatchReq`)**:
  ```json
  {
    "order_no": "ORD20240726001",
    "customer_phone": "13888888889",
    "delivery_address": "广州市天河区珠江新城",
    "delivery_fee": 150.00,
    "goods_weight": 2.5,
    "remark": "请在下午2-4点间派送"
  }
  ```
#### **2.4.9. 获取待派送订单列表**
- **Endpoint**: `GET /orders/fetch/{status}`
- **成功响应 (200 OK: `DispatchOrderFetchResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 5,
      "current": 1,
      "size": 10,
      "records": [
        {
          "order_no": "ORD20240726001",
          "customer_phone": "13888888889",
          "delivery_address": "广州市天河区珠江新城",
          "delivery_fee": 150.00,
          "goods_weight": 2.5,
          "create_time": "2024-07-26T15:00:00Z",
          "remark": "请在下午2-4点间派送"
        }
      ]
    }
  }
  ```

---

### **2.5. 选品单管理 (Selection Management)**

`基础路径: /selection`

#### **2.5.1. 分页查询选品单列表**
- **Endpoint**: `GET /selection/lists`
- **描述**: 供后台销售人员查看所有来自线上客户提交的意向单（选品单）。
- **请求参数 (Query Parameters)**:
  - `current` (Integer, Optional, default: 1): 当前页码。
  - `size` (Integer, Optional, default: 10): 每页数量。
  - `selection_no` (String, Optional): 按选品单号精确筛选。
  - `customer_phone` (String, Optional): 按客户手机号筛选。
  - `status` (Integer, Optional): 按处理状态筛选 (0=待跟进, 1=已联系, 2=已到店, 3=已失效/已转订单)。
- **成功响应 (200 OK: `SelectionListPagedResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 3,
      "current": 1,
      "size": 10,
      "records": [
        {
          "id": 1,
          "selection_no": "SEL20240726001",
          "customer_phone": "13900139000",
          "status": 0,
          "remark": "想了解下这两款瓷砖的耐磨性区别，方便的话请联系我。",
          "delivery_address": "广州市海珠区工业大道",
          "create_time": "2024-07-26T11:00:00Z",
          "update_time": "2024-07-26T11:00:00Z"
        }
      ]
    }
  }
  ```

#### **2.5.2. 查询选品单详情**
- **Endpoint**: `GET /selection/lists/{id}`
- **描述**: 查看指定选品单的详细内容，包括所有商品明细。
- **路径参数 (Path Variable)**: `id` (Long, Required).
- **成功响应 (200 OK: `List<SelectionItemsRecord>`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": 1,
        "item_model": "M-800x800-001",
        "item_specification": "800x800mm",
        "item_selling_price": 45.50,
        "amount": 50
      },
      {
        "id": 2,
        "item_model": "W-600x1200-003",
        "item_specification": "600x1200mm",
        "item_selling_price": 88.00,
        "amount": 30
      }
    ]
  }
  ```

#### **2.5.3. 更新选品单处理状态**
- **Endpoint**: `PUT /selection/lists/{id}/status/{status}`
- **描述**: 销售人员跟进后，手动更新选品单的状态。
- **路径参数 (Path Variable)**: `id` (Long, Required), `status` (Integer, Required).

#### **2.5.4. 修改选品单主信息**
- **Endpoint**: `PUT /selection/lists/{id}`
- **描述**: 修改客户电话、派送地址、备注等，不涉及商品明细。
- **路径参数 (Path Variable)**: `id` (Long, Required).
- **请求体 (Request Body: `SelectionListChangeReq`)**:
  ```json
  {
    "customer_phone": "13900139001",
    "delivery_address": "广州市海珠区工业大道XX小区XX栋",
    "remark": "客户已约好周日下午到店看样。"
  }
  ```
#### **2.5.5. 向选品单中添加新商品**
- **Endpoint**: `POST /selection/lists/{id}/items`
- **描述**: 当与客户沟通后，客户决定增加原来清单里没有的商品时调用。
- **路径参数 (Path Variable)**: `id` (Long, Required).
- **请求体 (Request Body: `SelectionItemAddReq`)**:
  ```json
  {
    "item_model": "GLUE-001",
    "item_selling_price": 50.00,
    "amount": 2
  }
  ```

#### **2.5.6. 修改选品单中某一项商品的数量**
- **Endpoint**: `PUT /selection/lists/{listId}/items/{itemId}`
- **路径参数 (Path Variable)**: `listId` (Long, Required), `itemId` (Long, Required).
- **请求参数 (Query Parameter)**: `amount` (Integer, Required).

#### **2.5.7. 从选品单中删除某一项商品**
- **Endpoint**: `DELETE /selection/lists/{listId}/items/{itemId}`
- **路径参数 (Path Variable)**: `listId` (Long, Required), `itemId` (Long, Required).

#### **2.5.8. 删除选品单**
- **Endpoint**: `DELETE /selection/lists/{id}`
- **描述**: 删除整个选品单及其所有商品项。
- **路径参数 (Path Variable)**: `id` (Long, Required).

#### **2.5.9. 选品单转为正式订单**
- **Endpoint**: `POST /selection/lists/order/{selectionListId}`
- **描述**: 将一个确认的选品单直接转化为正式订单，并自动扣减库存。
- **路径参数 (Path Variable)**: `selectionListId` (Long, Required).

---

### **2.6. 司机管理 (Driver Management)**

`基础路径: /manager`

#### **2.6.1. 获取司机列表**
- **Endpoint**: `GET /manager/driver-list`
- **成功响应 (200 OK: `DriverListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 3,
      "records": [
        {
          "id": 1,
          "name": "张师傅",
          "phone": "13612345678",
          "avatar": "https://example.com/driver1.jpg",
          "audit_status": 1,
          "work_status": 0,
          "openid": "wx_openid_string_1",
          "money": 1250.75,
          "create_time": "2024-07-20T10:00:00Z",
          "update_time": "2024-07-26T16:00:00Z"
        },
        {
          "id": 2,
          "name": "李师傅",
          "phone": "13787654321",
          "avatar": "https://example.com/driver2.jpg",
          "audit_status": 0,
          "work_status": 2,
          "openid": "wx_openid_string_2",
          "money": 0.00,
          "create_time": "2024-07-25T14:00:00Z",
          "update_time": "2024-07-25T14:00:00Z"
        }
      ]
    }
  }
  ```

#### **2.6.2. 司机管理操作**
- **同意司机资格**: `PUT /manager/driver-approval/{id}`
- **拒绝司机资格**: `PUT /manager/driver-rejection/{id}`
- **删除司机账户**: `DELETE /manager/driver-delete/{id}`
- **清零司机钱包**: `DELETE /manager/driver-reset-money/{id}`
- **路径参数 (Path Variable)** for all above: `id` (Long, Required).

---

### **2.7. 销售统计 (Sales Statistics)**

`基础路径: /sales`

#### **2.7.1. 获取周销量Top 5商品**
- **Endpoint**: `GET /sales/top-products`
- **成功响应 (200 OK: `List<SalesResp>`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "model": "M-800x800-001",
        "amount": 150
      },
      {
        "model": "W-600x1200-003",
        "amount": 80
      }
    ]
  }
  ```

#### **2.7.2. 获取销售趋势**
- **Endpoint**: `GET /sales/trend/{year}/{month}/{length}`
- **路径参数 (Path Variable)**: `year` (Int, Req), `month` (Int, Req), `length` (Int, Req).
- **成功响应 (200 OK: `List<SalesTrendResp>`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "total_price": 50000.00,
        "total_amount": 1100
      },
      {
        "total_price": 75000.00,
        "total_amount": 1500
      }
    ]
  }
  ```

---

### **2.8. 文件上传 (File Upload)**

`基础路径: /upload`

#### **2.8.1. 上传图片**
- **Endpoint**: `POST /upload/image`
- **请求类型**: `multipart/form-data`
- **请求组成**:
  - **Part 1 (File)**: `file` - 图像文件本身。
  - **Part 2 (Parameter)**: `itemId` (Long, Required) - 关联的库存商品ID。
- **成功响应 (200 OK)**:
  ```json
  {
    "url": "https://your-r2-storage.com/path/to/image.jpg"
  }
  ```

---

## **3. 司机与配送服务 (Delivery)**

### **3.1. 司机认证与状态 (Driver Auth & Status)**

`基础路径: /driver`

#### **3.1.1. 司机登录**
- **Endpoint**: `POST /driver/login`
- **请求参数 (Form Data)**: `code` (String, Req), `phone` (String, Req).
- **成功响应 (200 OK: `DriverInfoResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "name": "张师傅",
      "phone": "13612345678",
      "avatar": "https://example.com/driver1.jpg",
      "audit_status": 1,
      "work_status": 0,
      "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMzYxMjM0NTY3OCIsImlkIjoxLCJleHAiOjE2OTAwMDAwMDB9.hijklmn..."
    }
  }
  ```

#### **3.1.2. 获取司机审核状态**
- **Endpoint**: `GET /driver/audit-status/{id}`
- **成功响应 (200 OK)**:
  ```json
  { "code": 200, "message": "success", "data": 1 }
  ```

#### **3.1.3. 司机登出**
- **Endpoint**: `GET /driver/logout`
- **描述**: 司机退出登录，自动更新司机状态为离线并清除Token

#### **3.1.4. 更新司机工作状态**
- **Endpoint**: `POST /driver/info/change-status/{id}/{status}`
- **路径参数**: `id` (Long, Req), `status` (Int, Req: 0=空闲, 1=忙碌, 2=离线).

#### **3.1.5. 获取钱包信息**
- **Endpoint**: `GET /driver/info/wallet/{id}`
- **成功响应 (200 OK)**:
  ```json
  { "code": 200, "message": "success", "data": 1250.75 }
  ```
#### **3.1.6. 更新司机位置**
- **Endpoint**: `POST /driver/info/update-location`
- **请求参数 (Form Data)**: `id` (Long, Req), `latitude` (BigDecimal, Req), `longitude` (BigDecimal, Req).

---

### **3.2. 司机订单管理 (Delivery Management)**

`基础路径: /delivery`

#### **3.2.1. 获取司机已接订单列表**
- **Endpoint**: `GET /delivery/list`
- **成功响应 (200 OK: `DispatchOrderListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 1,
      "current": 1,
      "size": 10,
      "records": [
        {
          "id": 1,
          "order_no": "ORD20240726001",
          "driver_id": 1,
          "delivery_address": "广州市天河区珠江新城",
          "delivery_fee": 150.00,
          "goods_weight": 2.5,
          "remark": "请在下午2-4点间派送",
          "create_time": "2024-07-26T15:00:00Z",
          "update_time": "2024-07-26T15:10:00Z",
          "dispatch_status": 2
        }
      ]
    }
  }
  ```

#### **3.2.2. 获取可抢新订单**
- **Endpoint**: `GET /delivery/fetch/{status}`
- **描述**: `status`通常为`1`（待派送）
- **成功响应 (200 OK: `DispatchOrderFetchResp`)**:
  *结构与 2.4.9 节的 `DispatchOrderFetchResp` 相同。*

#### **3.2.3. 订单操作**
- **司机抢单**: `POST /delivery/rob/{id}/{orderNo}`
- **完成派送**: `POST /delivery/complete/{orderNo}`
- **取消派送**: `POST /delivery/cancel/{orderNo}`

---

### **3.3. 路线规划 (Route Planning)**

#### **3.3.1. 腾讯地图路线规划**
- **Endpoint**: `GET /route`
- **请求参数 (Query)**: `fromLat` (BigDecimal, Req), `toLat` (BigDecimal, Req), `fromLng` (BigDecimal, Req), `toLng` (BigDecimal, Req).
- **成功响应 (200 OK: `RouteResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "distance": 15000,
      "duration": 1800,
      "polyline": [
        [113.32, 23.13],
        [113.33, 23.14],
        [113.34, 23.15]
      ]
    }
  }
  ```

---

## **4. 线上商城服务 (Mall)**

### **4.1. 认证与授权 (Auth)**

`基础路径: /mall/auth`

#### **4.1.1. 获取匿名Token**
- **Endpoint**: `GET /mall/auth/anonymous-token`
- **成功响应 (200 OK)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": "eyJhbGciOiJIUzI1NiJ9.eyJjYXJ0SWQiOiJjYXJ0X2V4YW1wbGVfaWQiLCJleHAiOjE2OTAwMDAwMDB9.uvwxyz..."
  }
  ```

---

### **4.2. 商品展示 (Items Display)**

`基础路径: /mall/items`

#### **4.2.1. 查询商品列表**
- **Endpoint**: `GET /mall/items/list`
- **成功响应 (200 OK: `MallItemsListResp`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 28,
      "current": 1,
      "size": 10,
      "records": [
        {
          "model": "M-800x800-001",
          "manufacturer": "东鹏瓷砖",
          "specification": "800x800mm",
          "surface": 1,
          "category": 2,
          "total_amount": 1200,
          "selling_price": 45.50,
          "picture": "https://example.com/tile1.jpg"
        }
      ]
    }
  }
  ```

---

### **4.3. 购物车管理 (Cart Management)**

`基础路径: /mall/cart`

#### **4.3.1. 查看购物车**
- **Endpoint**: `GET /mall/cart`
- **成功响应 (200 OK: `List<CartItemsResp>`)**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "model": "M-800x800-001",
        "amount": 20
      },
      {
        "model": "W-600x1200-003",
        "amount": 10
      }
    ]
  }
  ```

#### **4.3.2. 添加/修改购物车商品**
- **添加**: `POST /mall/cart/add`
- **修改**: `POST /mall/cart/change`
- **请求体 (Request Body: `CartReq`)**:
  ```json
  {
    "model": "M-800x800-001",
    "amount": 25
  }
  ```

#### **4.3.3. 删除购物车商品**
- **Endpoint**: `DELETE /mall/cart/delete`
- **请求体 (Request Body: `CartDeleteReq`)**:
  ```json
  {
    "model": "W-600x1200-003"
  }
  ```

#### **4.3.4. 购物车下单(提交选品单)**
- **Endpoint**: `POST /mall/cart/order`
- **请求体 (Request Body: `MallOrderReq`)**:
  ```json
  {
    "customer_phone": "13900139000",
    "remark": "想了解下这两款瓷砖的耐磨性区别，方便的话请联系我。",
    "total_price": 3500.00,
    "delivery_address": "广州市海珠区工业大道",
    "items": [
      {
        "model": "M-800x800-001",
        "amount": 50
      },
      {
        "model": "W-600x1200-003",
        "amount": 30
      }
    ]
  }
  ```

---

### **4.4. 智能客服 (AI Chat)**

`基础路径: /mall/ai`

#### **4.4.1. AI流式聊天**
- **Endpoint**: `GET /mall/ai/stream-chat`
- **请求参数 (Query)**: `message` (String, Req), `sessionId` (String, Req).
- **响应**: `Content-Type: text/event-stream` (Server-Sent Events), 流式返回文本数据。
