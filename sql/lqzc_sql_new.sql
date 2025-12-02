CREATE DATABASE IF NOT EXISTS `lqzc_db_new`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE `lqzc_db_new`;

-- ----------------------------
-- 1. 瓷砖库存表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `inventory_item`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '库存ID',
    `model` VARCHAR(50) NOT NULL COMMENT '产品型号',
    `manufacturer` VARCHAR(50) NOT NULL COMMENT '制造厂商',
    `specification` VARCHAR(20) COMMENT '规格（如：600x600mm）',
    `surface` TINYINT COMMENT '表面处理（1=抛光 2=哑光 3=釉面 4=通体大理石 5=微晶石 6=岩板）',
    `category` TINYINT COMMENT '分类（1=墙砖 2=地砖 3=胶 4=洁具）',
    `warehouse_num` SMALLINT NOT NULL COMMENT '仓库编码',
    `total_amount` INT NOT NULL DEFAULT 0 COMMENT '总个数',
    `unit_per_box` INT DEFAULT 1 COMMENT '每箱个数',
    `picture` VARCHAR(256) DEFAULT NULL COMMENT '图片',
    `selling_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '销售单价（每片）',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `version` TINYINT DEFAULT 0 COMMENT '版本号',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_model_warehouse` (`model`, `warehouse_num`),
    KEY `idx_model_number` (`model`),
    KEY `idx_surface_category` (`surface`, `category`),
    CONSTRAINT `chk_pieces` CHECK (`total_amount` >= 0 AND `unit_per_box` > 0),
    CONSTRAINT `chk_warehouse` CHECK (`warehouse_num` >= 0 AND `warehouse_num` < 6)
    ) ENGINE=InnoDB COMMENT='瓷砖库存表';

-- ----------------------------
-- 2. 库存操作日志表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `inventory_log`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `item_id` BIGINT NOT NULL COMMENT '库存项ID',
    `log_type` TINYINT NOT NULL COMMENT '操作类型（1=入库 2=出库 3=调拨 4=冲正）',
    `amount_change` INT NOT NULL COMMENT '数量变化 (正数表示增加, 负数表示减少)',
    `source_warehouse` SMALLINT COMMENT '源仓库编码',
    `target_warehouse` SMALLINT COMMENT '目标仓库编码',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '操作备注',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_item_id` (`item_id`),
    CONSTRAINT `fk_inventory_log_item` FOREIGN KEY (`item_id`) REFERENCES `inventory_item` (`id`) ON DELETE RESTRICT
    ) ENGINE=InnoDB COMMENT='库存操作日志表';

-- ----------------------------
-- 3. 订单主表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `order_info`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '订单ID',
    `order_no` VARCHAR(30) NOT NULL UNIQUE COMMENT '订单编号',
    `customer_id` BIGINT DEFAULT NULL COMMENT '前台客户ID -- 新增字段',
    `customer_phone` VARCHAR(20) DEFAULT '' COMMENT '客户手机号',
    `order_source` TINYINT DEFAULT 1 COMMENT '订单来源(1=前台商城 2=管理后台 3=司机端) -- 新增字段',
    `total_price` DECIMAL(10,2) NOT NULL COMMENT '订单总金额(原始金额)',
    `payable_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '应付金额(扣除优惠后) -- 新增字段',
    `discount_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '优惠合计(积分/券) -- 新增字段',
    `dispatch_status` INT DEFAULT 0 COMMENT '订单派送状态：0=待派送 1=待接单 2=派送中 3=已完成',
    `order_status` TINYINT NOT NULL DEFAULT 0 COMMENT '订单状态：0=待支付 1=待发货 2=配送中 3=待确认(司机送达) 4=已完成 5=已取消 -- 新增字段',
    `pay_status` TINYINT NOT NULL DEFAULT 0 COMMENT '支付状态：0=未支付 1=已支付 2=部分退款 3=已退款 -- 新增字段',
    `pay_channel` TINYINT DEFAULT NULL COMMENT '支付渠道：1=微信 2=支付宝 3=银行卡 4=线下 -- 新增字段',
    `pay_time` DATETIME DEFAULT NULL COMMENT '支付时间 -- 新增字段',
    `delivery_fee` DECIMAL(10,2) DEFAULT 0.00 COMMENT '配送费用',
    `driver_id` BIGINT COMMENT '司机ID',
    `delivery_address` VARCHAR(100) DEFAULT NULL COMMENT '派送地址',
    `address_id` BIGINT DEFAULT NULL COMMENT '收货地址ID快照 -- 新增字段',
    `goods_weight` DECIMAL(10,2) COMMENT '货物重量(吨)',
    `coupon_id` BIGINT DEFAULT NULL COMMENT '使用的优惠券ID -- 新增字段',
    `points_used` INT DEFAULT 0 COMMENT '抵扣积分 -- 新增字段',
    `expected_delivery_time` DATETIME DEFAULT NULL COMMENT '期望送达时间 -- 新增字段',
    `receive_time` DATETIME DEFAULT NULL COMMENT '签收时间 -- 新增字段',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '订单备注',
    `cancel_reason` VARCHAR(200) DEFAULT NULL COMMENT '取消原因 -- 新增字段',
    `version` TINYINT DEFAULT 0 COMMENT '版本号',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '订单创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '订单更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_order_no` (`order_no`),
    KEY `idx_order_no` (`order_no`),
    KEY `idx_driver_id` (`driver_id`),
    KEY `idx_order_time` (`create_time`),
    KEY `idx_customer_phone` (`customer_phone`, `create_time`),
    KEY `idx_customer_order` (`customer_id`, `order_status`, `create_time`),
    KEY `idx_order_status` (`order_status`, `dispatch_status`)
    ) ENGINE=InnoDB COMMENT='订单主表';

-- ----------------------------
-- 4. 订单项表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `order_detail`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '订单项ID',
    `order_id` BIGINT NOT NULL COMMENT '订单ID',
    `item_id` BIGINT NOT NULL COMMENT '库存商品ID',
    `amount` INT NOT NULL COMMENT '购买数量',
    `subtotal_price` DECIMAL(10,2) NOT NULL COMMENT '小计金额',
    `version` TINYINT DEFAULT 0 COMMENT '版本号',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '订单项更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_order_id` (`order_id`),
    CONSTRAINT `fk_detail_order` FOREIGN KEY (`order_id`) REFERENCES `order_info` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_detail_inventory` FOREIGN KEY (`item_id`) REFERENCES `inventory_item` (`id`) ON DELETE RESTRICT
    ) ENGINE=InnoDB COMMENT='订单项表';

-- ----------------------------
-- 5. 选品单主表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `selection_list`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '选品单ID',
    `selection_no` VARCHAR(30) NOT NULL UNIQUE COMMENT '选品单编号 (例如：XPD20240725001)',
    `customer_phone` VARCHAR(20) DEFAULT NULL COMMENT '客户手机号 (可选填)',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '处理状态 (0=待跟进, 1=已联系, 2=已到店, 3=已失效)',
    `delivery_address` VARCHAR(255) DEFAULT NULL COMMENT '客户意向派送地址 (可选填)',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '客户备注',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_selection_no` (`selection_no`),
    KEY `idx_customer_phone` (`customer_phone`),
    KEY `idx_create_time` (`create_time`)
    ) ENGINE=InnoDB COMMENT='选品单主表';

-- ----------------------------
-- 6. 选品单明细表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `selection_item`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '选品明细ID',
    `selection_id` BIGINT NOT NULL COMMENT '所属选品单ID',
    `item_model` VARCHAR(50) NOT NULL COMMENT '产品型号 (不使用item_id，因为库存项可能会被删除)',
    `item_specification` VARCHAR(20) COMMENT '规格快照',
    `item_selling_price` DECIMAL(10,2) COMMENT '当时单价快照',
    `amount` INT NOT NULL COMMENT '意向数量',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_selection_id` (`selection_id`),
    CONSTRAINT `fk_item_to_list` FOREIGN KEY (`selection_id`) REFERENCES `selection_list` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB COMMENT='选品单明细表';

-- ----------------------------
-- 7. 前台客户账户 -- 新增表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `customer_user`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '客户ID',
    `nickname` VARCHAR(50) NOT NULL COMMENT '昵称',
    `phone` VARCHAR(20) NOT NULL COMMENT '手机号',
    `password` VARCHAR(100) DEFAULT NULL COMMENT '密码',
    `avatar` VARCHAR(255) DEFAULT '' COMMENT '头像URL',
    `email` VARCHAR(255) DEFAULT NULL COMMENT '邮箱',
    `gender` TINYINT DEFAULT 0 COMMENT '性别：0未知 1男 2女',
    `level` TINYINT DEFAULT 1 COMMENT '会员等级：1=普通 2=银卡 3=金卡 4=黑金',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1正常 0停用',
    `register_channel` VARCHAR(30) DEFAULT 'H5' COMMENT '注册渠道',
    `last_login_time` DATETIME DEFAULT NULL COMMENT '最近登录时间',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_customer_phone` (`phone`),
    KEY `idx_customer_level` (`level`, `status`)
    ) ENGINE=InnoDB COMMENT='前台客户账户';

-- ----------------------------
-- 7.1 会员等级配置 -- 新增表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `member_level`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `level` TINYINT NOT NULL COMMENT '等级：1=普通 2=银卡 3=金卡 4=黑金',
    `name` VARCHAR(50) NOT NULL COMMENT '等级名称',
    `min_points` INT NOT NULL DEFAULT 0 COMMENT '升级起始积分',
    `max_points` INT NOT NULL DEFAULT 2147483647 COMMENT '升级终止积分（闭区间）',
    `benefits` VARCHAR(255) DEFAULT NULL COMMENT '权益描述',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_level` (`level`)
    ) ENGINE=InnoDB COMMENT='会员等级配置';

-- ----------------------------
-- 8. 积分账户与流水 -- 新增表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `loyalty_points_account`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `balance` INT NOT NULL DEFAULT 0 COMMENT '当前可用积分',
    `total_earned` INT NOT NULL DEFAULT 0 COMMENT '累计获取',
    `total_spent` INT NOT NULL DEFAULT 0 COMMENT '累计消耗',
    `frozen` INT NOT NULL DEFAULT 0 COMMENT '冻结积分',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_customer_points` (`customer_id`)
    ) ENGINE=InnoDB COMMENT='客户积分账户';

CREATE TABLE IF NOT EXISTS `loyalty_points_log`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '流水ID',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `change_amount` INT NOT NULL COMMENT '积分变动（正加负扣）',
    `balance_after` INT NOT NULL COMMENT '变动后余额',
    `source_type` TINYINT NOT NULL COMMENT '来源：1下单赠送 2退款回退 3支付抵扣',
    `order_id` BIGINT DEFAULT NULL COMMENT '关联订单',
    `remark` VARCHAR(200) DEFAULT NULL COMMENT '备注',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_points_customer` (`customer_id`, `create_time`),
    KEY `idx_points_order` (`order_id`)
    ) ENGINE=InnoDB COMMENT='客户积分流水';

-- ----------------------------
-- 9. 优惠券 -- 新增表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `coupon_template`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '模板ID',
    `title` VARCHAR(80) NOT NULL COMMENT '优惠券标题',
    `type` TINYINT NOT NULL COMMENT '1=满减 2=折扣 3=现金券',
    `threshold_amount` DECIMAL(10,2) DEFAULT 0.00 COMMENT '使用门槛金额',
    `discount_amount` DECIMAL(10,2) DEFAULT 0.00 COMMENT '立减金额',
    `discount_rate` DECIMAL(4,2) DEFAULT 0.00 COMMENT '折扣（小数形式：0.90代表9折，优惠金额=总价×(1-折扣率)）',
    `max_discount` DECIMAL(10,2) DEFAULT NULL COMMENT '折扣封顶',
    `valid_from` DATETIME NOT NULL COMMENT '有效期开始',
    `valid_to` DATETIME NOT NULL COMMENT '有效期结束',
    `total_issued` INT DEFAULT 0 COMMENT '投放量',
    `per_user_limit` INT DEFAULT 1 COMMENT '每人限领',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0停用',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_coupon_date` (`valid_from`, `valid_to`),
    KEY `idx_coupon_status` (`status`)
    ) ENGINE=InnoDB COMMENT='优惠券模板';

CREATE TABLE IF NOT EXISTS `customer_coupon`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '券ID',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `template_id` BIGINT NOT NULL COMMENT '所属模板',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0未使用 1已使用 2已过期 3已作废',
    `code` VARCHAR(40) DEFAULT NULL COMMENT '券码',
    `obtained_channel` VARCHAR(30) DEFAULT '前台领取' COMMENT '获券渠道',
    `used_order_id` BIGINT DEFAULT NULL COMMENT '使用的订单',
    `use_time` DATETIME DEFAULT NULL COMMENT '使用时间',
    `expire_time` DATETIME DEFAULT NULL COMMENT '过期时间',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_coupon_customer` (`customer_id`, `status`),
    KEY `idx_coupon_template` (`template_id`)
    ) ENGINE=InnoDB COMMENT='客户优惠券';

-- ----------------------------
-- 10. 收货地址 -- 新增表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `customer_address`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '地址ID',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `receiver_name` VARCHAR(50) NOT NULL COMMENT '收货人',
    `receiver_phone` VARCHAR(20) NOT NULL COMMENT '收货人手机号',
    `province` VARCHAR(50) NOT NULL COMMENT '省份',
    `city` VARCHAR(50) NOT NULL COMMENT '城市',
    `district` VARCHAR(50) DEFAULT '' COMMENT '区县',
    `detail` VARCHAR(120) NOT NULL COMMENT '详细地址',
    `tag` VARCHAR(20) DEFAULT NULL COMMENT '标签（家/公司/工地）',
    `is_default` TINYINT DEFAULT 0 COMMENT '是否默认地址',
    `latitude` DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
    `longitude` DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_address_customer` (`customer_id`, `is_default`)
    ) ENGINE=InnoDB COMMENT='客户收货地址';

-- ----------------------------
-- 11. 订单支付与状态流水 -- 新增表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `order_payment`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '支付ID',
    `order_id` BIGINT NOT NULL COMMENT '订单ID',
    `pay_channel` TINYINT NOT NULL COMMENT '支付渠道：1=微信 2=支付宝 3=银行卡 4=线下',
    `pay_amount` DECIMAL(10,2) NOT NULL COMMENT '支付金额',
    `transaction_no` VARCHAR(64) DEFAULT NULL COMMENT '第三方交易号',
    `pay_status` TINYINT NOT NULL DEFAULT 0 COMMENT '0待支付 1成功 2失败 3退款中 4已退款',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_payment_order` (`order_id`, `pay_status`)
    ) ENGINE=InnoDB COMMENT='订单支付记录';

CREATE TABLE IF NOT EXISTS `order_status_history`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '历史ID',
    `order_id` BIGINT NOT NULL COMMENT '订单ID',
    `operator` VARCHAR(50) DEFAULT NULL COMMENT '操作人',
    `from_status` TINYINT DEFAULT NULL COMMENT '变更前状态',
    `to_status` TINYINT NOT NULL COMMENT '变更后状态',
    `remark` VARCHAR(200) DEFAULT NULL COMMENT '说明',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_history_order` (`order_id`, `create_time`)
    ) ENGINE=InnoDB COMMENT='订单状态变更记录';

-- 系统用户表
CREATE TABLE IF NOT EXISTS `user`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '登录账号',
    `password` VARCHAR(100) NOT NULL COMMENT '加密密码',
    `phone` VARCHAR(20) DEFAULT '' COMMENT '手机号',
    `avatar` VARCHAR(255) DEFAULT '' COMMENT '头像URL',
    `email` VARCHAR(255) DEFAULT NULL COMMENT '管理员email 同时也作为ems服务邮箱',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_username` (`username`),
    UNIQUE KEY `uniq_phone` (`phone`)
    ) ENGINE=InnoDB COMMENT='系统用户表';

-- 角色表
CREATE TABLE IF NOT EXISTS `role`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    `role_key` VARCHAR(100) NOT NULL COMMENT '角色标识',
    `description` VARCHAR(255) DEFAULT NULL COMMENT '角色描述',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_role_key` (`role_key`)
    ) ENGINE=InnoDB COMMENT='角色表';

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS `user_role`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `role_id` BIGINT NOT NULL COMMENT '角色ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_user_role` (`user_id`, `role_id`),
    KEY `idx_user_id` (`user_id`),
    CONSTRAINT `fk_user_role_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_role_role` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB COMMENT='用户角色关联表';

-- 司机信息表
CREATE TABLE IF NOT EXISTS `driver`
(
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '司机ID',
    `name` VARCHAR(50) NOT NULL COMMENT '司机姓名',
    `phone` VARCHAR(20) NOT NULL COMMENT '手机号',
    `avatar` VARCHAR(255) COMMENT '头像URL',
    `audit_status` TINYINT DEFAULT 0 COMMENT '审核状态(0=未审核,1=已通过,2=已拒绝)',
    `work_status` TINYINT DEFAULT 2 COMMENT '工作状态(0=空闲,1=忙碌,2=离线)',
    `openid` VARCHAR(100) COMMENT '微信OpenID',
    `money` DECIMAL(10,2) COMMENT '总金额',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_phone` (`phone`),
    UNIQUE KEY `uniq_openid` (`openid`),
    KEY `idx_status` (`work_status`),
    KEY `idx_audit_status` (`audit_status`)
    ) ENGINE=InnoDB COMMENT='司机信息表';

-- ====================================================================================
--  插入模拟数据
-- ====================================================================================
START TRANSACTION;

-- 会员等级示例（积分规则：1元=1积分，累计获取积分决定等级）
INSERT INTO `member_level` (`level`, `name`, `min_points`, `max_points`, `benefits`)
VALUES (1, '普通会员', 0, 1499, '下单积分'),
       (2, '银卡会员', 1500, 2999, '满减券/包邮'),
       (3, '金卡会员', 3000, 5999, '专属客服/生日券'),
       (4, '黑金会员', 6000, 2147483647, '高级客服/专属折扣')
    ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `max_points` = VALUES(`max_points`), `benefits` = VALUES(`benefits`), `update_time` = NOW();

-- 插入前台客户及积分、券示例
INSERT INTO `customer_user` (`id`, `nickname`, `phone`, `avatar`, `email`, `gender`, `level`, `status`, `register_channel`, `last_login_time`)
VALUES (1, '陈晨', '13800138001', 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200', 'chenchen@example.com', 1, 2, 1, 'H5', DATE_SUB(NOW(), INTERVAL 1 DAY)),
       (2, '刘涛', '13900139002', 'https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=200', NULL, 1, 1, 1, 'MiniApp', DATE_SUB(NOW(), INTERVAL 2 DAY)),
       (3, '李可心', '13700137003', 'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?w=200', 'lixin@example.com', 2, 3, 1, 'PC', NOW())
    ON DUPLICATE KEY UPDATE `nickname` = VALUES(`nickname`), `level` = VALUES(`level`), `status` = VALUES(`status`), `update_time` = NOW();

INSERT INTO `loyalty_points_account` (`customer_id`, `balance`, `total_earned`, `total_spent`, `frozen`)
VALUES (1, 3000, 4800, 1800, 0),
       (2, 860, 1260, 400, 0),
       (3, 150, 450, 300, 0)
    ON DUPLICATE KEY UPDATE `balance` = VALUES(`balance`), `total_earned` = VALUES(`total_earned`), `total_spent` = VALUES(`total_spent`), `update_time` = NOW();

-- 积分日志（积分规则：确认收货时按实付金额计算，1元=1积分）
INSERT INTO `loyalty_points_log` (`customer_id`, `change_amount`, `balance_after`, `source_type`, `order_id`, `remark`)
VALUES (1, 3400, 3400, 1, 1, '订单完成赠送积分(用户确认)'),
       (1, -200, 3200, 3, 1, '支付抵扣积分'),
       (1, -200, 3000, 3, NULL, '人工调整'),
       (2, 180, 860, 1, 2, '支付成功赠送积分'),
       (3, 150, 150, 2, NULL, '退款回退')
    ON DUPLICATE KEY UPDATE `remark` = VALUES(`remark`);

INSERT INTO `coupon_template` (`id`, `title`, `type`, `threshold_amount`, `discount_amount`, `discount_rate`, `max_discount`, `valid_from`, `valid_to`, `total_issued`, `per_user_limit`, `status`)
VALUES (1, '满299减30', 1, 299.00, 30.00, 0.00, NULL, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_ADD(NOW(), INTERVAL 30 DAY), 500, 2, 1),
       (2, '全场9折券', 2, 0.00, 0.00, 0.90, 150.00, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 15 DAY), 200, 1, 1),
       (3, '新人现金券5元', 3, 0.00, 5.00, 0.00, NULL, DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_ADD(NOW(), INTERVAL 20 DAY), 1000, 1, 1)
    ON DUPLICATE KEY UPDATE `status` = VALUES(`status`), `update_time` = NOW();

INSERT INTO `customer_coupon` (`id`, `customer_id`, `template_id`, `status`, `code`, `obtained_channel`, `used_order_id`, `use_time`, `expire_time`)
VALUES (1, 1, 1, 1, 'CC30OFF', '首页领券', 1, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_ADD(NOW(), INTERVAL 25 DAY)),
       (2, 1, 2, 0, 'VIP90', '会员赠送', NULL, NULL, DATE_ADD(NOW(), INTERVAL 12 DAY)),
       (3, 2, 3, 0, 'NEW5', '新人礼', NULL, NULL, DATE_ADD(NOW(), INTERVAL 20 DAY)),
       (4, 3, 1, 2, 'EXP30', '活动券', NULL, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY))
    ON DUPLICATE KEY UPDATE `status` = VALUES(`status`), `used_order_id` = VALUES(`used_order_id`), `update_time` = NOW();

INSERT INTO `customer_address` (`id`, `customer_id`, `receiver_name`, `receiver_phone`, `province`, `city`, `district`, `detail`, `tag`, `is_default`, `latitude`, `longitude`)
VALUES (1, 1, '陈晨', '13800138001', '广东省', '深圳市', '南山区', '科技园1号创新大厦', '公司', 1, 22.533500, 113.930400),
       (2, 2, '刘涛', '13900139002', '广东省', '广州市', '天河区', '珠江新城2号', '家', 1, 23.123400, 113.321100),
       (3, 3, '李可心', '13700137003', '广东省', '佛山市', '禅城区', '季华六路88号', '工地', 0, 23.021200, 113.110200)
    ON DUPLICATE KEY UPDATE `detail` = VALUES(`detail`), `is_default` = VALUES(`is_default`), `update_time` = NOW();

-- 插入角色数据（admin 和 employee）
INSERT INTO `role` (`role_key`, `description`)
VALUES ('admin', '系统管理员'), ('employee', '基础权限用户') ON DUPLICATE KEY UPDATE `update_time` = NOW();

-- 插入 admin 用户（密码为自定义密文）
INSERT INTO `user` (`username`, `password`, `phone`, `email`)
VALUES ('admin', 'adminzpaosuwqdnsauygdqwq', '13800138000', '13171351987@163.com') ON DUPLICATE KEY UPDATE `password` = '123123', `update_time` = NOW();

-- 绑定 admin 用户与 admin 角色
INSERT INTO `user_role` (`user_id`, `role_id`)
SELECT (SELECT `id` FROM `user` WHERE `username` = 'admin'),
       (SELECT `id` FROM `role` WHERE `role_key` = 'admin')
FROM DUAL
WHERE EXISTS (SELECT 1 FROM `user` WHERE `username` = 'admin')
  AND EXISTS (SELECT 1 FROM `role` WHERE `role_key` = 'admin') ON DUPLICATE KEY UPDATE `user_id` = `user_id`;

-- 插入 player 用户（密码为明文123456的MD5加密 e10adc3949ba59abbe56e057f20f883e）
INSERT INTO `user` (`username`, `password`, `phone`, `email`)
VALUES ('player', 'e10adc3949ba59abbe56e057f20f883e', '', NULL) ON DUPLICATE KEY UPDATE `update_time` = NOW();

-- 绑定 player 用户与 employee 角色
INSERT INTO `user_role` (`user_id`, `role_id`)
SELECT (SELECT `id` FROM `user` WHERE `username` = 'player'),
       (SELECT `id` FROM `role` WHERE `role_key` = 'employee')
FROM DUAL
WHERE EXISTS (SELECT 1 FROM `user` WHERE `username` = 'player')
  AND EXISTS (SELECT 1 FROM `role` WHERE `role_key` = 'employee') ON DUPLICATE KEY UPDATE `user_id` = `user_id`;

-- 插入库存数据（修正重复ID问题）
INSERT INTO `inventory_item` (`id`, `model`, `manufacturer`, `specification`, `surface`, `category`, `warehouse_num`,
                              `total_amount`, `unit_per_box`, `picture`, `selling_price`, `remark`)
VALUES (1, 'A8001', '佛山陶瓷一厂', '800x800mm', 1, 2, 1, 349, 4,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/10.png', 25.50, '经典抛光地砖'),
       (2, 'B6002', '广东宏大陶瓷', '600x600mm', 2, 1, 1, 750, 6,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/3.png', 18.00, '哑光防滑墙砖'),
       (3, 'A8002', '佛山陶瓷一厂', '800x800mm', 4, 2, 2, 964, 4,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/2.png', 25.50, '二号仓备货'),
       (4, 'C9003-GREY', '新中源陶瓷', '900x900mm', 6, 2, 2, 179, 2,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/6.png', 88.00, '高端岩板-灰色'),
       (5, 'M6001', '东鹏瓷砖', '600x600mm', 5, 2, 1, 200, 4,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/4.png', 3.80, '抛光地砖，耐磨抗污'),
       (6, 'M6002', '诺贝尔瓷砖', '600x600mm', 2, 2, 2, 157, 4,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/7.png', 4.50, '哑光表面，适合客厅'),
       (7, 'M6003', '诺贝尔瓷砖', '600x600mm', 2, 2, 3, 120, 4,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/8.png', 4.50, '哑光表面，适合卧室'),
       (8, 'W3001', '马可波罗', '300x600mm', 3, 1, 1, 300, 6,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/1.png', 2.50, '釉面墙砖，简约风格'),
       (9, 'W3002', '东鹏瓷砖', '300x600mm', 3, 1, 2, 250, 6,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/9.png', 2.80, '釉面墙砖，灰色调'),
       (10, 'Y12001', '简一瓷砖', '1200x2400mm', 6, 2, 1, 62, 1,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/image%20(1).jpg', 38.00, '岩板，适合高端装修'),
       (11, 'Y12002', '大角鹿', '1200x2400mm', 6, 2, 2, 50, 1,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/image.jpg', 42.00, '岩板，进口材质'),
       (12, 'G1001', '东方雨虹', NULL, NULL, 3, 1, 500, 1,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed12.png', 12.00, '强力瓷砖胶，20kg包装'),
       (13, 'T001', '箭牌卫浴', '700x380x750mm', NULL, 4, 1, 80, 1,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed10.png', 480.00, '一体式马桶，缓降盖板'),
       (14, 'T002', '九牧卫浴', '680x370x760mm', NULL, 4, 2, 60, 1,
        'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed11.png', 520.00, '节水型马桶，虹吸式冲洗'),
       -- 修正重复ID问题：将原重复的id=2、3改为15、16
       (15, 'B6009', '广东宏大陶瓷', '600x600mm', 2, 1, 1, 750, 6, 'https://example.com/img/b6002.jpg', 18.00,
        '哑光防滑墙砖'),
       (16, 'A80012', '佛山陶瓷一厂', '800x800mm', 1, 2, 2, 1000, 4, 'https://example.com/img/a8001.jpg', 25.50,
        '二号仓备货');

-- 2. 插入订单数据
-- 订单1: 已完成（状态4）- 司机送达后用户已确认收货
INSERT INTO `order_info` (`id`, `order_no`, `customer_id`, `customer_phone`, `order_source`, `total_price`, `payable_amount`,
                          `discount_amount`, `dispatch_status`, `order_status`, `pay_status`, `pay_channel`, `driver_id`,
                          `delivery_address`, `address_id`, `delivery_fee`, `goods_weight`, `coupon_id`,
                          `points_used`, `pay_time`, `receive_time`, `remark`)
VALUES (1, 'ORD202310270001', 1, '13800138001', 1, 3450.00, 3400.00, 50.00, 3, 4, 1, 1, 1,
        '广东省深圳市南山区科技园1号', 1, 50.00, 3.60, 1, 200,
        DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), '客户要求下午派送');

-- 订单2: 待发货（状态1）- 后台已确认支付，等待派送
INSERT INTO `order_info` (`id`, `order_no`, `customer_id`, `customer_phone`, `order_source`, `total_price`, `payable_amount`,
                          `discount_amount`, `dispatch_status`, `order_status`, `pay_status`, `pay_channel`, `coupon_id`,
                          `delivery_address`, `address_id`, `delivery_fee`, `goods_weight`, `remark`, `pay_time`)
VALUES (2, 'ORD202310270002', 2, '13900139002', 1, 1760.00, 1760.00, 0.00, 1, 1, 1, 2, NULL,
        '广东省广州市天河区珠江新城2号', 2, 30.00, 2.10, '加急处理，送货上门', DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 3. 插入订单项数据
INSERT INTO `order_detail` (`order_id`, `item_id`, `amount`, `subtotal_price`)
VALUES (1, 1, 100, 2550.00),  -- 购买了100片 id=1 的 A8001
       (1, 2, 50, 900.00);    -- 购买了50片 id=2 的 B6002

INSERT INTO `order_detail` (`order_id`, `item_id`, `amount`, `subtotal_price`)
VALUES (2, 4, 20, 1760.00);  -- 购买了20片 id=4 的 C9003-GREY

-- 3.1 插入订单支付记录
INSERT INTO `order_payment` (`order_id`, `pay_channel`, `pay_amount`, `transaction_no`, `pay_status`, `create_time`)
VALUES (1, 1, 3400.00, 'WX202310270001', 1, DATE_SUB(NOW(), INTERVAL 5 DAY)),
       (2, 2, 1760.00, 'ALI202310270002', 1, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 3.2 插入订单状态流转（状态：0待支付 1待发货 2配送中 3待确认 4已完成 5已取消）
INSERT INTO `order_status_history` (`order_id`, `operator`, `from_status`, `to_status`, `remark`, `create_time`)
VALUES (1, 'system', 0, 1, '后台确认支付', DATE_SUB(NOW(), INTERVAL 5 DAY)),
       (1, 'system', 1, 2, '司机接单开始配送', DATE_SUB(NOW(), INTERVAL 4 DAY)),
       (1, 'system', 2, 3, '司机送达等待确认', DATE_SUB(NOW(), INTERVAL 3 DAY)),
       (1, 'system', 3, 4, '用户确认收货', DATE_SUB(NOW(), INTERVAL 2 DAY)),
       (2, 'system', 0, 1, '后台确认支付，待发货', DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 4. 插入库存操作日志 (模拟出库)
INSERT INTO `inventory_log` (`item_id`, `log_type`, `amount_change`, `source_warehouse`, `remark`)
VALUES (1, 2, -100, 1, '订单ORD202310270001销售出库'),
       (2, 2, -50, 1, '订单ORD202310270001销售出库');

INSERT INTO `inventory_log` (`item_id`, `log_type`, `amount_change`, `source_warehouse`, `remark`)
VALUES (4, 2, -20, 2, '订单ORD202310270002销售出库');

COMMIT;
