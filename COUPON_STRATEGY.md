# 优惠券策略引擎设计说明

> 目标：把优惠券计算从散落的 if/switch 抽离为“策略 + 模板方法 + 计算器”三段式，做到可插拔、新券种低侵入，并在订单预览/结算中统一复用。

## 1. 角色划分

- `CouponDiscountStrategy`：策略接口，定义 `getType` / `canApply` / `calculateDiscount`。
- `AbstractCouponDiscountStrategy`：模板方法封装通用校验（类型匹配、有效期、门槛），再委派子类计算。
- 具体策略（按 `coupon_template.type`）：
  - `FullReductionCouponStrategy` (type=1)：满减，校验立减金额非负。
  - `DiscountRateCouponStrategy` (type=2)：折扣，校验折扣率 (0,1)，支持封顶 `maxDiscount`。
  - `CashCouponStrategy` (type=3)：现金立减，校验金额非负。
- `CouponCalculator`：策略路由 + 对外统一入口，负责：
  1) 根据模板 type 找策略并调用 `canApply`/`calculateDiscount`
  2) `findBestCoupon`：在用户持有的券里挑选最大优惠（返回券、模板、优惠金额的组合）。

## 2. 流程示意

```
controller/service -> CouponCalculator
    ├─ canApply(template, totalPrice)
    ├─ calculateDiscount(template, totalPrice)
    └─ findBestCoupon(coupons, templateMap, totalPrice)

CouponCalculator
    └─ 按 type 找到策略 (strategyMap[type])
        └─ AbstractCouponDiscountStrategy.canApply
            ├─ 通用校验：非空/type匹配/有效期/门槛
            └─ extraValidate (子类特有)
        └─ AbstractCouponDiscountStrategy.calculateDiscount
            ├─ 先 canApply
            └─ doCalculate (子类计算优惠)
```

## 3. 核心方法实现要点

### AbstractCouponDiscountStrategy
- `canApply`：
  - 判空、类型一致性
  - 有效期校验：`validFrom <= now <= validTo`
  - 门槛校验：`totalPrice >= thresholdAmount`
  - 钩子 `extraValidate`：子类补充前置条件
- `calculateDiscount`：
  - 先跑 `canApply`，不可用返回 0
  - 调用子类 `doCalculate`，对结果做非负保护

### FullReductionCouponStrategy (type=1)
- `extraValidate`：`discountAmount >= 0`
- `doCalculate`：返回 `discountAmount`

### DiscountRateCouponStrategy (type=2)
- `extraValidate`：`0 < discountRate < 1`
- `doCalculate`：
  - `discount = totalPrice * (1 - discountRate)`
  - 若 `maxDiscount` 非空，则 `min(discount, maxDiscount)`

### CashCouponStrategy (type=3)
- `extraValidate`：`discountAmount >= 0`
- `doCalculate`：返回 `discountAmount`

### CouponCalculator
- 构造注入 `List<CouponDiscountStrategy>`，构建 `strategyMap<type, strategy>`。
- `canApply`/`calculateDiscount`：找不到策略返回 false/0。
- `findBestCoupon`：
  - 入参：用户持有的 `CustomerCoupon` 列表、`templateId -> CouponTemplate` 映射、订单总价
  - 遍历每张券：用模板查策略计算优惠，选出金额最大的，返回 `BestCoupon(coupon, template, discount)`。

## 4. 业务接入点

- 订单预览/下单：`src/main/java/com/lqzc/controller/MallOrderController.java`
  - 预览：指定券或自动匹配最佳券 -> `CouponCalculator.calculateDiscount`/`findBestCoupon`
  - 下单：校验券可用 -> 计算优惠 -> 写入订单金额与券 ID
- 后台确认支付：`src/main/java/com/lqzc/service/impl/OrderInfoServiceImpl.java`
  - 支付确认时计算优惠 -> 更新订单金额并标记券已用

## 5. 扩展与测试

- 新券种：新增 `CouponDiscountStrategy` 实现（可继承 Abstract 复用校验），只需设置 `getType` 与 `doCalculate`/`extraValidate`，无需修改业务调用方。
- 单测：`src/test/java/com/lqzc/coupon/CouponCalculatorTests.java`
  - 覆盖门槛、折扣封顶、最优券选择，验证策略与路由正确性。

## 6. 设计收益（对面试可讲）

- 解耦：业务层不再关心券种细节，只用 `CouponCalculator` 统一入口。
- 可扩展：新增券种零侵入业务代码，符合开闭原则。
- 可测试：策略纯函数化，易于单元测试；通用校验集中，减少重复与漏校验。
