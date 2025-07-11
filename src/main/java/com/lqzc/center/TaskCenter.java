package com.lqzc.center;


import com.lqzc.common.constant.RedisConstant;
import com.lqzc.common.domain.SaleRecord;
import com.lqzc.mapper.UserMapper;
import com.mongodb.DuplicateKeyException;
import jakarta.annotation.Resource;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

@Service
@EnableScheduling
public class TaskCenter {
    @Resource
    private UserMapper userMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private MongoTemplate mongoTemplate;
    @Resource
    private AnalysisCenter analysisCenter;
    @Resource
    private EmailCenter emailCenter;

    //每周日晚九点 将redis的所有卖品("model",amount)同步到mongodb ZSCAN
//    @Scheduled(cron = "0 0 21 ? * SUN")
//    public void dataSwapRedis2Mongo() {
//        String sourceKey = RedisConstant.HOT_SALES;
//        String archiveKey = RedisConstant.HOT_SALES_ARCHIVE;
//
//        // 原子地创建快照，并检查操作是否真的执行了
//        Boolean renamed;
//        try {
//            renamed = stringRedisTemplate.renameIfAbsent(sourceKey, archiveKey);
//        } catch (Exception e) {
//            System.out.println("执行RENAME操作时Redis发生异常！任务中断。");
//            return;
//        }
//
//        // 如果源Key不存在(renamed=false)，则无需进行任何后续操作，任务正常结束
//        if (!renamed) {
//            System.out.println("源Key 不存在，无需迁移，任务正常结束。");
//            return;
//        }
//        // 为快照设置过期时间，作为兜底
//        stringRedisTemplate.expire(archiveKey, 7, TimeUnit.DAYS);
//
//        // 只有在RENAME成功后，才继续下面的步骤
//        boolean migrationSuccess = false;
//        try {
//            // 使用 try-with-resources 确保 cursor 被关闭 cursor(智能迭代器)
//            try (Cursor<ZSetOperations.TypedTuple<String>> cursor = stringRedisTemplate.opsForZSet()
//                    //scan 输入参数：key option：count
//                    .scan(archiveKey, ScanOptions.scanOptions().count(RedisConstant.BATCH_SIZE).build())) {
//
//                String formattedDate = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
//                List<SaleRecord> batchDocs = new ArrayList<>(RedisConstant.BATCH_SIZE);
//
//                while (cursor.hasNext()) {
//                    ZSetOperations.TypedTuple<String> tuple = cursor.next();
//                    SaleRecord record = new SaleRecord();
//                    record.setModel(tuple.getValue());
//                    record.setAmount(tuple.getScore() != null ? tuple.getScore().intValue() : 0);
//                    record.setSyncDate(formattedDate);
//                    batchDocs.add(record);
//                    //只有到了一批的阈值才会处理插入，并清理batchDocs 如果没到到阈值结束循环
//                    if (batchDocs.size() >= RedisConstant.BATCH_SIZE) {
//                        insertBatchToMongo(batchDocs);
//                        batchDocs.clear();
//                    }
//                }
//                //如果没到到阈值结束循环 不为空接着插入
//                if (!batchDocs.isEmpty()) {
//                    insertBatchToMongo(batchDocs);
//                }
//            }
//
//            migrationSuccess = true;
//
//        } catch (Exception e) {
//            // 迁移过程中发生了错误，记录日志。migrationSuccess 依然是 false。
//            System.out.println("数据迁移过程中发生严重错误！源快照将被保留以供排查。");
//        }
//
//        // 3. 根据迁移结果，决定是删除快照还是让它自动过期
//        if (migrationSuccess) {
//            stringRedisTemplate.delete(archiveKey);
//            System.out.println("迁移成功，已清理归档Key。");
//        } else {
//
//            System.out.println("迁移失败，归档Key将被保留14天以便排查问题。");
//        }
//    }

//    每周日晚九点 将redis的所有卖品("model",amount)同步到mongodb
//    @Scheduled(cron = "0 0 21 ? * SUN")
    public void dataSwapRedis2Mongo() {
        String sourceKey = RedisConstant.HOT_SALES;
        String archiveKey = RedisConstant.HOT_SALES_ARCHIVE;

        //原子地创建快照，并检查操作是否真的执行了
        Boolean renamed;
        try {
            renamed = stringRedisTemplate.renameIfAbsent(sourceKey, archiveKey);
        } catch (Exception e) {
            System.out.println("执行RENAME操作时Redis发生异常！任务中断。");
            return;
        }

        //如果源Key不存在(renamed=false)，则无需进行任何后续操作，任务正常结束
        if (!renamed) {
            System.out.println("源Key 不存在，无需迁移，任务正常结束。");
            return;
        }
        //为快照设置过期时间，作为兜底
        stringRedisTemplate.expire(archiveKey, 7, TimeUnit.DAYS);

        List<SaleRecord> docs = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd"); // 格式化为 年-月-日
        String formattedDate = sdf.format("yyyy-MM-dd");
        boolean migrationSuccess = false;

        Set<ZSetOperations.TypedTuple<String>> typedTuples =
                //要用reverseRangeWithScores 如果popMax拿不到数据
                stringRedisTemplate.opsForZSet().reverseRangeWithScores(archiveKey, 0,-1);
        try {
            if (typedTuples != null) {
                for (ZSetOperations.TypedTuple<String> tuple : typedTuples) {
                    SaleRecord record = new SaleRecord();
                    Double score = tuple.getScore();
                    record.setModel(tuple.getValue());
                    if (score != null) {
                        record.setAmount(score.intValue());
                    }
                    record.setSyncDate(formattedDate); // 改为字符串形式的日期
                    docs.add(record);
                }
                mongoTemplate.insert(docs, "hot_sales");
                migrationSuccess = true;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }

        if (migrationSuccess) {
            stringRedisTemplate.delete(archiveKey);
            System.out.println("迁移成功，已清理归档Key。");
        } else {

            System.out.println("迁移失败，归档Key将被保留7天以便排查问题。");
        }
    }

    /**
     * 封装的MongoDB批量插入方法，内部处理幂等性冲突。
     */
    private void insertBatchToMongo(List<SaleRecord> docs) {
        if (docs == null || docs.isEmpty()) {
            return;
        }
        try {
            mongoTemplate.insert(docs, "hot_sales");
        } catch (DuplicateKeyException e) {
            // 精准捕获幂等性冲突，视为警告
            System.out.println("批量插入MongoDB时出现重复键冲突，可安全忽略。");
        }
    }

    // 每月1号的早上8点执行
//    @Scheduled(cron = "0 0 8 1 * ?")
    public void generateAndSendMonthlyReport() {
        try {
            String adminEmail = userMapper.getAdminEmail();
            // 1. 调用核心分析服务
            String reportContent = analysisCenter.generateMonthlyAnalysisReport();
            // 2. 发送邮件
            if (reportContent != null && !reportContent.isEmpty()) {
                emailCenter.sendEmail(adminEmail, "月度销售经营分析报告", reportContent);
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

}
