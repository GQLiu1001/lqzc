package com.lqzc.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.lqzc.common.domain.SelectionList;
import com.baomidou.mybatisplus.extension.service.IService;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.req.SelectionListChangeReq;

/**
* @author rabbittank
* @description 针对表【selection_list(选品单主表)】的数据库操作Service
* @createDate 2025-07-11 09:05:49
*/
public interface SelectionListService extends IService<SelectionList> {

    /**
     * 更新选品单状态
     *
     * @param id     选品单ID
     * @param status 目标状态
     */
    void updateSelectionStatus(Long id, Integer status);

    /**
     * 分页查询选品单列表
     * <p>
     * 支持按选品单编号、客户手机号和状态筛选。
     * </p>
     *
     * @param page          分页对象
     * @param selectionNo   选品单编号
     * @param customerPhone 客户手机号
     * @param status        状态
     * @return 选品单分页数据
     */
    IPage<SelectionList> getSelectionList(IPage<SelectionList> page, String selectionNo, String customerPhone, Integer status);

    /**
     * 更新选品单信息
     *
     * @param req 选品单变更请求
     * @param id  选品单ID
     */
    void updateSelectionList(SelectionListChangeReq req, Long id);

    /**
     * 删除选品单
     *
     * @param id 选品单ID
     */
    void deleteSelectionList(Long id);

    /**
     * 新增选品单
     * <p>
     * 创建新的选品单（商城下单场景）。
     * </p>
     *
     * @param mallOrderReq 商城订单请求
     * @return 新建选品单ID
     */
    Long addSellectionList(MallOrderReq mallOrderReq);
}
