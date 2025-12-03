<div align="center">
  <h1>🏢 LQZC 瓷砖商城管理系统</h1>
  <p>一个现代化的瓷砖商城全栈管理系统，集成库存管理、订单处理、智能派送、C端商城、优惠券秒杀和AI客服功能</p>
  
  <p>
    <img src="https://img.shields.io/badge/Java-17-orange?style=flat-square&logo=openjdk" alt="Java">
    <img src="https://img.shields.io/badge/Spring%20Boot-3.3.3-brightgreen?style=flat-square&logo=spring" alt="Spring Boot">
    <img src="https://img.shields.io/badge/MySQL-8.0-blue?style=flat-square&logo=mysql" alt="MySQL">
    <img src="https://img.shields.io/badge/Redis-7.0-red?style=flat-square&logo=redis" alt="Redis">
    <img src="https://img.shields.io/badge/MyBatis--Plus-3.5-blueviolet?style=flat-square" alt="MyBatis-Plus">
  </p>
</div>

## 📋 项目简介

LQZC 瓷砖商城管理系统是一个功能完整的企业级瓷砖销售管理平台，为瓷砖零售商提供从库存管理到订单配送的全流程数字化解决方案。系统采用现代化架构，集成了**高并发优惠券秒杀**、AI智能客服、实时数据分析和智能派送调度等先进功能。

## ✨ 核心功能

### 🎫 高并发优惠券秒杀系统（⭐核心亮点）
- **Redis Cluster + Lua脚本防超发**: 6节点集群，原子性操作保证库存一致性
- **分布式锁初始化**: SETNX确保库存只初始化一次
- **RabbitMQ异步削峰**: 消息队列解耦，提升系统吞吐量
- **多实例水平扩展**: 2实例集群，支持动态扩容
- **经压测验证**: 2800瞬时并发、QPS 1460+、P95 103ms、错误率0%、零超发
- **支持多种券类型**: 满减券、折扣券、现金券

### 🏪 C端商城系统
- **客户账户**: 注册、登录、个人信息管理
- **收货地址**: 多地址管理、默认地址设置
- **积分系统**: 下单赠送、支付抵扣、流水记录
- **会员等级**: 根据累计积分自动升级
- **订单管理**: 完整的订单生命周期管理

### 📦 库存管理
- **多仓库管理**: 支持多个仓库的库存统一管理
- **实时库存**: 库存数量实时更新和预警
- **库存日志**: 详细的出入库操作记录和追踪
- **乐观锁防超卖**: MyBatis-Plus @Version实现

### 🚚 智能派送系统
- **司机管理**: 司机注册、审核和状态管理
- **订单派送**: 智能订单分配和派送状态跟踪
- **路线规划**: 集成腾讯地图API的最优路线规划
- **实时定位**: 派送过程的实时位置追踪

### 👥 用户权限管理
- **多角色系统**: 管理员、普通用户、司机等角色权限控制
- **JWT认证**: 基于JWT的安全认证机制
- **C端Token**: UUID Token存储于Redis，支持7天有效期

### 🤖 AI智能客服
- **阿里云通义千问**: 集成阿里云AI大模型
- **智能对话**: 支持商品咨询和业务问答
- **流式响应**: Server-Sent Events实时推送

### 📊 数据分析
- **销售统计**: 实时销售数据统计和排行
- **月度报告**: 自动生成月度销售分析报告
- **热销商品**: 基于Redis的热销商品排行榜

## 🏗️ 项目架构图

![image-20250614222403102](https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/%E6%9C%AA%E5%91%BD%E5%90%8D%E7%BB%98%E5%9B%BE.drawio%20(1).png)

## 🛠️ 技术栈

### 后端技术
| 技术 | 版本 | 说明 |
|------|------|------|
| Spring Boot | 3.3.3 | 核心框架 |
| MySQL | 8.0 | 关系型数据库 |
| MyBatis Plus | 3.5 | ORM框架 |
| Redis Cluster | 7.0 | 6节点集群（3主3从） |
| Lua脚本 | - | 原子性抢券操作 |
| RabbitMQ | 3.x | 消息队列异步削峰 |
| JWT | - | 认证授权 |
| SpringDoc | 3 | API文档 |

### AI与集成服务
- **AI模型**: 阿里云通义千问 (DashScope)
- **地图服务**: 腾讯地图API
- **微信集成**: 微信小程序SDK
- **云存储**: Cloudflare R2
- **邮件服务**: Jakarta Mail

## 🚀 快速开始

### 环境要求
- Java 17+
- MySQL 8.0+
- Redis 7.0+（支持Cluster模式）
- RabbitMQ 3.x+
- Maven 3.8+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/lqzc.git
cd lqzc
```

2. **数据库初始化**
```bash
mysql -u root -p < sql/lqzc_db.sql
```

3. **配置文件**
```bash
cp src/main/resources/application.yaml.example src/main/resources/application.yaml
# 修改数据库、Redis等配置
```

4. **启动服务**
```bash
# 启动Redis（或Redis Cluster）
redis-server

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
│   ├── aspect/              # AOP切面（性能监控）
│   ├── common/              # 公共组件
│   │   ├── domain/          # 实体类
│   │   ├── req/             # 请求DTO
│   │   └── resp/            # 响应DTO
│   ├── config/              # 配置类
│   ├── controller/          # 控制器（含Mall、Admin）
│   ├── mapper/              # 数据访问层
│   ├── service/             # 业务逻辑层
│   └── utils/               # 工具类
├── src/main/resources/
│   ├── application.yaml     # 主配置文件
│   └── mapper/              # MyBatis映射文件
├── api/
│   └── api-doc.md           # 完整API文档
├── sql/
│   └── lqzc_db.sql          # 数据库脚本（含所有表）
└── scripts/
    ├── batch_register.py    # 压测用户批量注册脚本
    └── 压测说明.md          # 压测文档及结果
```

## 🎫 优惠券秒杀系统详解

### 技术方案
- **Redis Cluster预扣库存**: 6节点集群（3主3从），库存缓存到Redis，避免数据库压力
- **Lua脚本原子操作**: 检查库存→检查限领→扣减库存，一步完成
- **分布式锁初始化**: 使用SETNX确保库存只初始化一次
- **RabbitMQ异步削峰**: 抢券成功后异步入库，降低数据库压力
- **多实例水平扩展**: 2实例集群，线性提升吞吐量

### 核心代码
```lua
-- Lua脚本：原子性抢券
local stock = tonumber(redis.call('get', KEYS[1]) or 0)
if stock <= 0 then return 0 end  -- 库存不足
local received = tonumber(redis.call('get', KEYS[2]) or 0)
if received >= tonumber(ARGV[1]) then return -1 end  -- 已达上限
redis.call('decr', KEYS[1])
redis.call('incr', KEYS[2])
return 1  -- 成功
```

### 压测结果（2实例 + 6节点Redis集群）

| 指标 | 2800并发/1秒（稳定） | 3000并发/1秒（极限） |
|------|---------------------|---------------------|
| 峰值QPS | **1460** | 1439 |
| P95响应 | **103ms** | 785ms |
| 平均响应 | 43ms | 348ms |
| 错误率 | 0% | 0% |
| 超发情况 | 无 | 无 |

> 详细压测报告见 `scripts/压测说明.md`

## 📖 API文档

项目集成了SpringDoc OpenAPI 3，详细API文档见 [api/api-doc.md](api/api-doc.md)

### 主要模块
| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| 后台用户 | `/user` | 管理员登录、用户管理 |
| 库存管理 | `/inventory` | 商品、库存、日志 |
| 订单管理 | `/orders` | 订单CRUD、派送 |
| 司机服务 | `/driver`, `/delivery` | 司机端功能 |
| C端客户 | `/mall/customer` | 注册、登录、个人信息 |
| C端优惠券 | `/mall/coupon` | 领券、我的券 |
| C端订单 | `/mall/order` | 下单、支付、确认收货 |
| 后台优惠券 | `/admin/coupon` | 创建、管理优惠券 |
| 后台积分 | `/admin/points` | 积分流水、调整 |

## 🔒 安全特性

- **JWT认证**: 无状态的用户认证
- **角色权限**: 基于角色的访问控制
- **乐观锁**: 防止库存超卖
- **Lua原子操作**: 防止优惠券超发
- **密码加密**: BCrypt密码加密存储

## 🎯 核心特色

### 1. 高并发优惠券秒杀
经过JMeter压测验证，**2实例+6节点Redis集群**在2800瞬时并发场景下稳定运行，QPS达1460+，P95响应103ms，零超发。

### 2. 完整C端功能
涵盖客户账户、收货地址、积分会员、优惠券、订单支付全流程。

### 3. 智能AI客服
集成阿里云通义千问，提供流式响应的智能客服功能。

### 4. 智能派送调度
集成腾讯地图API，支持最优路线规划和实时位置追踪。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

<div align="center">
  <p>⭐ 如果这个项目对你有帮助，请给它一个星标！</p>
  <p>Made with ❤️ by Rabbittank</p>
</div>
