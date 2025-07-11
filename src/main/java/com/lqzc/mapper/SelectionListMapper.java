package com.lqzc.mapper;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.SelectionList;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;

/**
* @author 11965
* @description 针对表【selection_list(选品单主表)】的数据库操作Mapper
* @createDate 2025-07-11 09:05:49
* @Entity com.lqzc.common.domain.SelectionList
*/
public interface SelectionListMapper extends BaseMapper<SelectionList> {
    IPage<SelectionList> getSelectionList(IPage<SelectionList> page, String selectionNo, String customerPhone, Integer status);
}




