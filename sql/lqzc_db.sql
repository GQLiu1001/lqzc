CREATE DATABASE IF NOT EXISTS `lqzc_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE `lqzc_db`;

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
    `customer_phone` VARCHAR(20) DEFAULT '' COMMENT '客户手机号',
    `total_price` DECIMAL(10,2) NOT NULL COMMENT '订单总金额',
    `dispatch_status` INT DEFAULT 0 COMMENT '订单派送状态：0=待派送 1=待接单 2=派送中 3=已完成',
    `driver_id` BIGINT COMMENT '司机ID',
    `delivery_address` VARCHAR(100) DEFAULT NULL COMMENT '派送地址',
    `delivery_fee` DECIMAL(10,2) DEFAULT 0.00 COMMENT '配送费用',
    `goods_weight` DECIMAL(10,2) COMMENT '货物重量(吨)',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '订单备注',
    `version` TINYINT DEFAULT 0 COMMENT '版本号',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '订单创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '订单更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_order_no` (`order_no`),
    KEY `idx_order_no` (`order_no`),
    KEY `idx_driver_id` (`driver_id`),
    KEY `idx_order_time` (`create_time`),
    KEY `idx_customer_phone` (`customer_phone`, `create_time`)
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
INSERT INTO `order_info` (`id`, `order_no`, `customer_phone`, `total_price`, `dispatch_status`, `driver_id`,
                          `delivery_address`, `delivery_fee`, `remark`)
VALUES (1, 'ORD202310270001', '13800138001', 3450.00, 3, 1, '广东省深圳市南山区科技园1号', 50.00, '客户要求下午派送');

INSERT INTO `order_info` (`id`, `order_no`, `customer_phone`, `total_price`, `dispatch_status`, `delivery_address`,
                          `delivery_fee`)
VALUES (2, 'ORD202310270002', '13900139002', 1760.00, 1, '广东省广州市天河区珠江新城2号', 30.00);

-- 3. 插入订单项数据
INSERT INTO `order_detail` (`order_id`, `item_id`, `amount`, `subtotal_price`)
VALUES (1, 1, 100, 2550.00),  -- 购买了100片 id=1 的 A8001
       (1, 2, 50, 900.00);    -- 购买了50片 id=2 的 B6002

INSERT INTO `order_detail` (`order_id`, `item_id`, `amount`, `subtotal_price`)
VALUES (2, 4, 20, 1760.00);  -- 购买了20片 id=4 的 C9003-GREY

-- 4. 插入库存操作日志 (模拟出库)
INSERT INTO `inventory_log` (`item_id`, `log_type`, `amount_change`, `source_warehouse`, `remark`)
VALUES (1, 2, -100, 1, '订单ORD202310270001销售出库'),
       (2, 2, -50, 1, '订单ORD202310270001销售出库');

INSERT INTO `inventory_log` (`item_id`, `log_type`, `amount_change`, `source_warehouse`, `remark`)
VALUES (4, 2, -20, 2, '订单ORD202310270002销售出库');

COMMIT;