package com.lqzc.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.MemberLevel;
import com.lqzc.mapper.MemberLevelMapper;
import com.lqzc.service.MemberLevelService;
import org.springframework.stereotype.Service;

/**
* @author 11965
* @description 针对表【member_level(会员等级配置)】的数据库操作Service实现
* @createDate 2025-12-02 00:00:00
*/
@Service
public class MemberLevelServiceImpl extends ServiceImpl<MemberLevelMapper, MemberLevel>
    implements MemberLevelService {

}

