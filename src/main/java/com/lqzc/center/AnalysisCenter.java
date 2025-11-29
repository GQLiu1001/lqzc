//package com.lqzc.center;
//
//import com.lqzc.common.domain.SaleRecord;
//import jakarta.annotation.Resource;
//import org.springframework.data.mongodb.core.MongoTemplate;
//import org.springframework.data.mongodb.core.query.Criteria;
//import org.springframework.data.mongodb.core.query.Query;
//import org.springframework.stereotype.Service;
//
//import java.text.SimpleDateFormat;
//import java.util.*;
//
//@Service
//public class AnalysisCenter {
////    @Resource
////    private MongoTemplate mongoTemplate;
////
////    public String generateMonthlyAnalysisReport() {
////
////        // === 1. 确定上个月的日期格式, 例如 "2025-05" ===
////        Calendar cal = Calendar.getInstance();
////        cal.add(Calendar.MONTH, -1); // 获取上个月的日历
////        String lastMonthPattern = new SimpleDateFormat("yyyy-MM").format(cal.getTime());
////
////        // === 2. 从 MongoDB 查询上个月的数据 ===
////        // 构造查询条件：查询 syncDate 字段以 "2025-05" 开头的所有文档
////        Query query = new Query(Criteria.where("syncDate").regex("^" + lastMonthPattern));
////
////        // 直接查询出所有匹配的文档列表
////        // 注意：这里的 SaleRecord 是一个简单的Java类，用来接收MongoDB的数据
////        List<SaleRecord> monthlyRecords = mongoTemplate.find(query, SaleRecord.class, "hot_sales");
////
////        // 如果上个月没有任何销售记录，就返回提示信息
////        if (monthlyRecords.isEmpty()) {
////            return String.format("【%s】月份无销售数据，报告未生成。", lastMonthPattern);
////        }
////
////        // === 3. 在 Java 内存中进行聚合计算 ===
////        Map<String, Integer> salesMap = new HashMap<>();
////        for (SaleRecord record : monthlyRecords) {
////            // 如果Map中已有该商品，就在原有数量上累加；如果没有，就新增。
////            //merge 是 Java 8 中 Map 接口新增的方法。用一行代码解决“如果key存在就更新，不存在就新增”的常见问题。
////            salesMap.merge(record.getModel(), record.getAmount(), Integer::sum);
////        }
////
////        // === 4. 拼接邮件报告内容 ===
////        StringBuilder reportBuilder = new StringBuilder();
////        reportBuilder.append(String.format("尊敬的管理员，这是【%s】的销售数据报告：\n\n", lastMonthPattern));
////
////        // 按销量从高到低排个序
////        //Map 的设计初衷是快速查找，它内部没有顺序的概念。把它转换成一个 List，然后对 List 进行排序
////        //List的存储类型是Map.Entry<String, Long> salesMap.entrySet()可以直接当作内容填充
////        //public ArrayList(Collection<? extends E> c) 这个构造函数，可以把任何 Collection 接口的子类或实现类，都转换成一个 ArrayList。
////        List<Map.Entry<String, Integer>> sortedSales = new ArrayList<>(salesMap.entrySet());
////        //sort 方法接受一个 Comparator (比较器) 作为参数，告诉它排序的规则。 默认override了Comparator方法
////        //根据 Comparator 的规定，返回正数意味着第一个参数（在这里是e1）大于第二个参数（e2）。-> 排序算法认为 e1 “更大”，应该排在后面。
////        //compareTo 方法的返回值符号，决定了 o1 相对于 o2 的排序位置。
////        //e1.compareTo(e2): e1 和 e2 按自然顺序（升序）比较。
////        //e2.compareTo(e1): 颠倒了比较的双方，所以结果就是自然顺序的反向（降序）。
////        sortedSales.sort((e1, e2) -> e2.getValue().compareTo(e1.getValue()));
////
////        // 遍历排序后的结果，生成报告
////        for (Map.Entry<String, Integer> entry : sortedSales) {
////            String model = entry.getKey();
////            Integer totalAmount = entry.getValue();
////
////            String formattedLine = String.format(
////                    "• 商品型号【%s】: 销量 %d 件\n",
////                    model,
////                    totalAmount
////            );
////            reportBuilder.append(formattedLine);
////        }
////
////        return reportBuilder.toString();
////    }
//}
