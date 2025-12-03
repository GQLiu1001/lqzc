package com.lqzc.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.lqzc.common.domain.LoyaltyPointsAccount;
import com.lqzc.common.domain.LoyaltyPointsLog;
import com.lqzc.common.exception.LianqingAdminException;
import com.lqzc.common.req.PointsAdjustReq;
import com.lqzc.common.resp.PointsLogItemResp;
import com.lqzc.mapper.LoyaltyPointsAccountMapper;
import com.lqzc.mapper.LoyaltyPointsLogMapper;
import com.lqzc.service.LoyaltyPointsLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;

/**
 * 积分流水服务实现类
 *
 * @author rabbittank
 * @description 针对表【loyalty_points_log(客户积分流水)】的数据库操作Service实现
 * @createDate 2025-07-11 09:05:49
 */
@Service
@RequiredArgsConstructor
public class LoyaltyPointsLogServiceImpl extends ServiceImpl<LoyaltyPointsLogMapper, LoyaltyPointsLog>
        implements LoyaltyPointsLogService {

    private final LoyaltyPointsLogMapper loyaltyPointsLogMapper;
    private final LoyaltyPointsAccountMapper loyaltyPointsAccountMapper;

    /**
     * 分页查询积分流水记录
     */
    @Override
    public IPage<PointsLogItemResp> getPointsLogList(IPage<PointsLogItemResp> page, String customerPhone, Integer sourceType, String startDate, String endDate) {
        return loyaltyPointsLogMapper.selectPointsLogList(page, customerPhone, sourceType, startDate, endDate);
    }

    /**
     * 人工调整积分
     * <p>
     * 业务流程：
     * 1. 校验客户积分账户是否存在
     * 2. 校验扣减时积分是否充足
     * 3. 更新积分账户余额
     * 4. 创建流水记录
     * </p>
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void adjustPoints(PointsAdjustReq req) {
        // 1. 查询客户积分账户
        LoyaltyPointsAccount account = loyaltyPointsAccountMapper.selectOne(
                new LambdaQueryWrapper<LoyaltyPointsAccount>()
                        .eq(LoyaltyPointsAccount::getCustomerId, req.getCustomerId())
        );
        if (account == null) {
            throw new LianqingAdminException("客户积分账户不存在");
        }

        // 2. 校验扣减时积分是否充足
        int newBalance = account.getBalance() + req.getChangeAmount();
        if (newBalance < 0) {
            throw new LianqingAdminException("积分不足，当前余额：" + account.getBalance());
        }

        // 3. 更新积分账户
        account.setBalance(newBalance);
        if (req.getChangeAmount() > 0) {
            account.setTotalEarned(account.getTotalEarned() + req.getChangeAmount());
        } else {
            account.setTotalSpent(account.getTotalSpent() + Math.abs(req.getChangeAmount()));
        }
        account.setUpdateTime(new Date());
        loyaltyPointsAccountMapper.updateById(account);

        // 4. 创建流水记录
        LoyaltyPointsLog log = new LoyaltyPointsLog();
        log.setCustomerId(req.getCustomerId());
        log.setChangeAmount(req.getChangeAmount());
        log.setBalanceAfter(newBalance);
        log.setSourceType(4); // 4=人工调整
        log.setRemark(req.getRemark() != null ? req.getRemark() : "人工调整积分");
        log.setCreateTime(new Date());
        loyaltyPointsLogMapper.insert(log);
    }
}
