package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.SelectionList;
import com.lqzc.common.exception.LianqingException;
import com.lqzc.common.req.MallOrderReq;
import com.lqzc.common.req.SelectionListChangeReq;
import com.lqzc.service.SelectionListService;
import com.lqzc.mapper.SelectionListMapper;
import com.lqzc.utils.OrderNumberGenerator;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * @author rabbittank
 * @description 针对表【selection_list(选品单主表)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
public class SelectionListServiceImpl extends ServiceImpl<SelectionListMapper, SelectionList>
        implements SelectionListService {

    @Resource
    private SelectionListMapper selectionListMapper;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void updateSelectionStatus(Long id, Integer status) {
        SelectionList selectionList = selectionListMapper.selectById(id);
        selectionList.setStatus(status);
        selectionListMapper.updateById(selectionList);
    }

    @Override
    public IPage<SelectionList> getSelectionList(IPage<SelectionList> page, String selectionNo, String customerPhone, Integer status) {
        return selectionListMapper.getSelectionList(page, selectionNo, customerPhone, status);

    }

    @Override
    public Long addSellectionList(MallOrderReq mallOrderReq) {
        SelectionList selectionList = new SelectionList();
        BeanUtils.copyProperties(mallOrderReq, selectionList);
        String selectionNo = OrderNumberGenerator.generateSelectionListNumber();
        selectionList.setSelectionNo(selectionNo);
        selectionList.setStatus(0);
        int insert = selectionListMapper.insert(selectionList);
        if (insert != 1) {
            throw new LianqingException("插入selectionListMapper失败");
        }
        return selectionList.getId();
    }

    @Transactional(rollbackFor = Exception.class)
    @Override
    public void updateSelectionList(SelectionListChangeReq req, Long id) {
        SelectionList selectionList = selectionListMapper.selectById(id);
        if (req.getCustomerPhone() != null) {
            selectionList.setCustomerPhone(req.getCustomerPhone());
        }
        if (req.getRemark() != null) {
            selectionList.setRemark(req.getRemark());
        }
        if (req.getDeliveryAddress() != null) {
            selectionList.setDeliveryAddress(req.getDeliveryAddress());
        }
        selectionListMapper.updateById(selectionList);
    }

    @Override
    public void deleteSelectionList(Long id) {
        LambdaQueryWrapper<SelectionList> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(SelectionList::getId, id);
        selectionListMapper.delete(queryWrapper);
    }

}




