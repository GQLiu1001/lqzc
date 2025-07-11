package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.SelectionList;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.req.SelectionListChangeReq;

/**
* @author 11965
* @description 针对表【selection_list(选品单主表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface SelectionListService extends IService<SelectionList> {
    void updateSelectionStatus(Long id, Integer status);

    IPage<SelectionList> getSelectionList(IPage<SelectionList> page, String selectionNo, String customerPhone, Integer status);

    void updateSelectionList(SelectionListChangeReq req, Long id);

    void deleteSelectionList(Long id);

    Long addSellectionList(MallOrderReq mallOrderReq);
}
