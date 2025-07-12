<div align="center">
  <h1>🏢 LQZC 瓷砖商城管理系统</h1>
  <p>一个现代化的瓷砖商城全栈管理系统，集成库存管理、订单处理、智能派送和AI客服功能</p>
  
  <p>
    <img src="https://img.shields.io/badge/Java-21-orange?style=flat-square&logo=openjdk" alt="Java">
    <img src="https://img.shields.io/badge/Spring%20Boot-3.3.3-brightgreen?style=flat-square&logo=spring" alt="Spring Boot">
    <img src="https://img.shields.io/badge/MySQL-8.0-blue?style=flat-square&logo=mysql" alt="MySQL">
    <img src="https://img.shields.io/badge/Redis-7.0-red?style=flat-square&logo=redis" alt="Redis">
    <img src="https://img.shields.io/badge/MongoDB-6.0-green?style=flat-square&logo=mongodb" alt="MongoDB">
    <img src="https://img.shields.io/badge/RabbitMQ-3.12-orange?style=flat-square&logo=rabbitmq" alt="RabbitMQ">
  </p>
</div>

## 📋 项目简介

LQZC 瓷砖商城管理系统是一个功能完整的企业级瓷砖销售管理平台，为瓷砖零售商提供从库存管理到订单配送的全流程数字化解决方案。系统采用现代化的微服务架构，集成了AI智能客服、实时数据分析和智能派送调度等先进功能。

## ✨ 核心功能

### 🏪 商城系统
- **商品展示**: 瓷砖产品的多维度展示和分类浏览
- **购物车**: 支持匿名用户和登录用户的购物车功能
- **订单管理**: 完整的订单生命周期管理
- **选品单**: 客户意向商品收集和跟进管理

### 📦 库存管理
- **多仓库管理**: 支持多个仓库的库存统一管理
- **实时库存**: 库存数量实时更新和预警
- **库存日志**: 详细的出入库操作记录和追踪
- **商品分类**: 按表面处理、规格、厂商等多维度分类

### 🚚 智能派送系统
- **司机管理**: 司机注册、审核和状态管理
- **订单派送**: 智能订单分配和派送状态跟踪
- **路线规划**: 集成腾讯地图API的最优路线规划
- **实时定位**: 派送过程的实时位置追踪

### 👥 用户权限管理
- **多角色系统**: 管理员、普通用户、司机等角色权限控制
- **JWT认证**: 基于JWT的安全认证机制
- **用户信息管理**: 完整的用户资料管理功能

### 🤖 AI智能客服
- **阿里云通义千问**: 集成阿里云AI大模型
- **智能对话**: 支持商品咨询和业务问答
- **销售数据查询**: AI工具函数支持销售数据智能查询
- **对话记忆**: 基于数据库的对话上下文记忆

### 📊 数据分析
- **销售统计**: 实时销售数据统计和排行
- **月度报告**: 自动生成月度销售分析报告
- **热销商品**: 基于Redis的热销商品排行榜
- **趋势分析**: 销售趋势和数据可视化

## 🛠️ 技术栈

### 后端技术
- **框架**: Spring Boot 3.3.3
- **数据库**: MySQL 8.0 + MyBatis Plus
- **缓存**: Redis + Redisson
- **文档数据库**: MongoDB
- **消息队列**: RabbitMQ
- **认证**: JWT + Spring Security
- **API文档**: SpringDoc OpenAPI 3

### AI与集成服务
- **AI模型**: 阿里云通义千问 (DashScope)
- **地图服务**: 腾讯地图API
- **微信集成**: 微信小程序SDK
- **云存储**: AWS S3
- **邮件服务**: Jakarta Mail

### 开发工具
- **构建工具**: Maven
- **代码简化**: Lombok
- **AOP**: AspectJ
- **HTTP客户端**: RestTemplate

## 🚀 快速开始

### 环境要求
- Java 21+
- MySQL 8.0+
- Redis 7.0+
- MongoDB 6.0+
- RabbitMQ 3.12+
- Maven 3.8+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/lqzc.git
cd lqzc
```

2. **数据库初始化**
```bash
# 导入数据库结构和初始数据
mysql -u root -p < sql/lqzc_db.sql
```

3. **配置文件**
```bash
# 复制配置文件模板
cp src/main/resources/application.yaml.example src/main/resources/application.yaml
# 或者创建开发环境配置
cp src/main/resources/application.yaml.example src/main/resources/application-dev.yaml
# 根据你的环境修改配置文件中的占位符
```

4. **启动服务**
```bash
# 启动Redis
redis-server

# 启动MongoDB
mongod

# 启动RabbitMQ
rabbitmq-server

# 启动应用
mvn spring-boot:run
```

5. **访问应用**
- API文档: http://localhost:8001/swagger-ui.html
- 应用接口: http://localhost:8001

## 📁 项目结构

```
lqzc/
├── src/main/java/com/lqzc/
│   ├── aspect/              # AOP切面
│   ├── center/              # 数据分析中心
│   ├── common/              # 公共组件
│   │   ├── constant/        # 常量定义
│   │   ├── domain/          # 实体类
│   │   ├── enums/           # 枚举类
│   │   ├── exception/       # 异常处理
│   │   ├── records/         # 记录类
│   │   ├── req/             # 请求DTO
│   │   └── resp/            # 响应DTO
│   ├── config/              # 配置类
│   ├── controller/          # 控制器
│   ├── mapper/              # 数据访问层
│   ├── service/             # 业务逻辑层
│   └── utils/               # 工具类
├── src/main/resources/
│   ├── mapper/              # MyBatis映射文件
│   ├── application.yaml     # 主配置文件
│   ├── application-dev.yaml # 开发环境配置
│   └── application-prod.yaml# 生产环境配置
└── sql/
    └── lqzc_db.sql          # 数据库脚本
```

## 🔧 配置说明

### 配置文件模板

项目提供了配置文件模板 `application.yaml.example`，包含所有必要的配置项。请按以下步骤配置：

1. **复制模板文件**
```bash
# 创建主配置文件
cp src/main/resources/application.yaml.example src/main/resources/application.yaml

# 或创建开发环境配置
cp src/main/resources/application.yaml.example src/main/resources/application-dev.yaml
```

2. **修改配置占位符**

### 数据库配置
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/lqzc_db?useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
    username: your_mysql_username  # 替换为实际的MySQL用户名
    password: your_mysql_password  # 替换为实际的MySQL密码
    driver-class-name: com.mysql.cj.jdbc.Driver
```

### Redis配置
```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      database: 0
      password: your_redis_password  # 如果Redis没有密码，删除此行
```

### MongoDB配置
```yaml
spring:
  data:
    mongodb:
      host: localhost
      port: 27017
      database: lqzcbase
      # 如果需要认证，取消注释并填入实际值
      # username: your_mongodb_username
      # password: your_mongodb_password
```

### AI配置 (阿里云通义千问)
```yaml
spring:
  ai:
    dashscope:
      api-key: your_dashscope_api_key  # 替换为实际的DashScope API密钥
      base-url: https://dashscope.aliyuncs.com/compatible-mode/v1
      chat:
        options:
          model: qwen-max-latest
```

### 微信小程序配置
```yaml
wx:
  miniapp:
    appId: your_wechat_app_id      # 替换为实际的微信小程序AppID
    secret: your_wechat_app_secret  # 替换为实际的微信小程序Secret
```

### 腾讯地图API配置
```yaml
tencent:
  map:
    key: your_tencent_map_api_key  # 替换为实际的腾讯地图API密钥
```

### 邮件服务配置
```yaml
spring:
  mail:
    host: smtp.163.com  # 根据邮箱提供商修改
    port: 465
    username: your_email@example.com     # 替换为实际邮箱
    password: your_email_auth_code       # 替换为邮箱授权码（非登录密码）
    properties:
      mail:
        smtp:
          ssl:
            enable: true
          auth: true
```

### Cloudflare R2存储配置
```yaml
cloudflare:
  r2:
    bucket-name: your_bucket_name           # 替换为实际的存储桶名称
    endpoint: https://your_account_id.r2.cloudflarestorage.com
    access-key-id: your_access_key_id       # 替换为实际的访问密钥ID
    secret-access-key: your_secret_access_key  # 替换为实际的机密访问密钥
    public-url: https://your_custom_domain.r2.dev  # 替换为实际的公共访问URL
```

### JWT安全配置
```yaml
jwt:
  secret: "your-super-secret-key-that-is-at-least-32-characters-long"  # 使用强密码
  expiration:
    anonymous: 30d
```

### 🔒 安全提醒

- ⚠️ **配置文件已被.gitignore忽略**，确保敏感信息不会被提交到版本控制
- 🔑 **使用强密码**：JWT密钥至少32位字符
- 📧 **邮箱授权码**：使用邮箱的授权码，不是登录密码
- 🔐 **API密钥安全**：定期轮换API密钥，避免泄露

## 📖 API文档

项目集成了SpringDoc OpenAPI 3，启动应用后可访问：
- Swagger UI: http://localhost:8001/swagger-ui.html
- OpenAPI JSON: http://localhost:8001/v3/api-docs
- 详细API文档: [api/api-doc.md](api/api-doc.md)

### 🏗️ 微服务架构

系统采用微服务架构，包含以下服务：

#### 1. 后台管理核心服务 (Consul) - `http://localhost:8001`
**用户管理模块** `/user`
- `POST /user/login` - 用户登录
- `POST /user/logout` - 用户登出
- `POST /user/register` - 用户注册
- `POST /user/reset-password` - 重置密码
- `GET /user/list` - 用户列表查询
- `POST /user/modify-info` - 修改用户信息
- `DELETE /user/delete/{id}` - 删除用户

**库存管理模块** `/inventory`
- `GET /inventory/list` - 库存商品列表
- `POST /inventory/modify` - 修改库存信息
- `DELETE /inventory/delete/{id}` - 删除库存商品
- `GET /inventory/fetch/{model}` - 根据型号查询库存

**库存日志模块** `/inventory-log`
- `GET /inventory-log/list` - 库存日志列表
- `POST /inventory-log/create-inbound` - 创建入库日志
- `POST /inventory-log/create-transfer` - 创建调拨日志
- `POST /inventory-log/modify` - 修改库存日志
- `DELETE /inventory-log/delete/{id}` - 删除库存日志

**订单管理模块** `/orders`
- `POST /orders/create` - 创建订单
- `GET /orders/list` - 订单列表查询
- `GET /orders/detail/{orderNo}` - 订单详情
- `POST /orders/modify` - 修改订单主信息
- `POST /orders/modify-sub-items` - 修改订单子项
- `DELETE /orders/delete/{orderNo}` - 删除订单
- `POST /orders/change-dispatch-status` - 修改派送状态
- `POST /orders/create-dispatch` - 创建派送单
- `GET /orders/fetch-pending` - 获取待派送订单

**选品单管理模块** `/selection`
- `GET /selection/list` - 选品单列表
- `GET /selection/detail/{id}` - 选品单详情
- `POST /selection/update-status` - 更新选品单状态
- `POST /selection/modify-main-info` - 修改选品单主信息
- `POST /selection/add-item` - 添加选品单商品
- `POST /selection/modify-item` - 修改选品单商品
- `DELETE /selection/delete-item/{id}` - 删除选品单商品
- `DELETE /selection/delete/{id}` - 删除选品单
- `POST /selection/convert-to-order` - 选品单转订单

**司机管理模块** `/driver`
- `GET /driver/list` - 司机列表
- `POST /driver/approve/{id}` - 审核通过司机
- `POST /driver/reject/{id}` - 拒绝司机申请
- `DELETE /driver/delete/{id}` - 删除司机
- `POST /driver/reset-money/{id}` - 重置司机余额

**销售统计模块** `/sales`
- `GET /sales/top-products` - 热销商品排行
- `GET /sales/sales-trend` - 销售趋势分析

#### 2. 司机与派送服务 (Delivery) - `http://localhost:8002`
**派送管理模块** `/delivery`
- `GET /delivery/list` - 司机已接订单列表
- `GET /delivery/fetch/{status}` - 获取可抢新订单
- `POST /delivery/rob/{id}/{orderNo}` - 司机抢单
- `POST /delivery/complete/{orderNo}` - 完成派送
- `POST /delivery/cancel/{orderNo}` - 取消派送

**路线规划模块** `/route`
- `GET /route` - 腾讯地图路线规划
  - 参数: `fromLat`, `toLat`, `fromLng`, `toLng`
  - 返回: 距离、时长、路线坐标

#### 3. 线上商城服务 (Mall) - `http://localhost:8003`
**认证授权模块** `/mall/auth`
- `GET /mall/auth/anonymous-token` - 获取匿名Token

**商品展示模块** `/mall/items`
- `GET /mall/items/list` - 商品列表查询
  - 支持分页、筛选、排序
  - 返回商品型号、厂商、规格、价格等信息

**购物车管理模块** `/mall/cart`
- `GET /mall/cart` - 查看购物车
- `POST /mall/cart/add` - 添加商品到购物车
- `POST /mall/cart/change` - 修改购物车商品数量
- `DELETE /mall/cart/delete` - 删除购物车商品
- `POST /mall/cart/order` - 购物车下单(提交选品单)

**AI智能客服模块** `/mall/ai`
- `GET /mall/ai/stream-chat` - AI流式聊天
  - 参数: `message`, `sessionId`
  - 返回: Server-Sent Events流式响应

### 📋 API响应格式

所有API遵循统一的响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体数据内容
  }
}
```

**状态码说明:**
- `200` - 请求成功
- `400` - 请求参数错误
- `401` - 未授权访问
- `403` - 权限不足
- `404` - 资源不存在
- `500` - 服务器内部错误

### 🔐 认证机制

- **JWT Token**: 用户登录后获取JWT令牌
- **Token传递**: 请求头中携带 `Authorization: Bearer <token>`
- **匿名访问**: 商城部分接口支持匿名Token访问
- **权限控制**: 基于角色的API访问权限控制

## 🔒 安全特性

- **JWT认证**: 无状态的用户认证
- **角色权限**: 基于角色的访问控制
- **AOP切面**: 统一的权限校验
- **密码加密**: BCrypt密码加密存储
- **SQL注入防护**: MyBatis Plus预编译语句

## 🎯 核心特色

### 1. 智能AI客服
集成阿里云通义千问大模型，提供智能客服功能，支持：
- 商品咨询和推荐
- 销售数据查询
- 业务流程指导
- 多轮对话记忆

### 2. 实时数据分析
基于Redis和MongoDB的实时数据分析：
- 热销商品实时排行
- 销售趋势分析
- 自动月度报告生成

### 3. 智能派送调度
集成腾讯地图API的智能派送系统：
- 最优路线规划
- 实时位置追踪
- 智能订单分配

### 4. 多端支持
- Web管理后台
- 微信小程序
- 移动端司机APP

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

<div align="center">
  <p>⭐ 如果这个项目对你有帮助，请给它一个星标！</p>
  <p>Made with ❤️ by Rabbittank</p>
</div>