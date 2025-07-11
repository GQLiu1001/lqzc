package com.lqzc.common.resp;

import com.lqzc.common.records.UserListRecord;
import lombok.Data;
import java.util.List;

/**
 * 用户列表响应类
 * total current size List:UserListRecord records
 */
@Data
public class UserListResp {
    /**
     * 总记录数
     */
    private Long total;
    
    /**
     * 当前页
     */
    private Long current;
    
    /**
     * 每页大小
     */
    private Long size;
    
    /**
     * 用户记录列表
     */
    private List<UserListRecord> records;

} 