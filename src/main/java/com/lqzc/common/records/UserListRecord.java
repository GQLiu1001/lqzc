package com.lqzc.common.records;

import lombok.Data;

/**
 * 用户记录内部类
 * 涉及User子字段以及单独的roleKey
 * @author Rabbittank
 * @since 1.0.0
 */
@Data
public class UserListRecord {
    /**
     * 用户ID
     */
    private Long id;

    /**
     * 用户名
     */
    private String username;

    /**
     * 手机号
     */
    private String phone;

    /**
     * 角色标识
     */
    private Long roleId;
}