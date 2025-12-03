package com.lqzc.mapper;

import com.lqzc.common.domain.Driver;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
* @author rabbittank
* @description 针对表【driver(司机信息表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.Driver
*/
public interface DriverMapper extends BaseMapper<Driver> {
    @Select("select * from driver")
    List<Driver> getDriverList();
}




