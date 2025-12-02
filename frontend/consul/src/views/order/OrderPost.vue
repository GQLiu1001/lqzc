<!--创建订单-->
<script setup lang="ts">
import { ref, computed, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { UserFilled, User, Notebook, Search } from '@element-plus/icons-vue';
import { postOrder } from '@/api/order';
import { useUserStore } from '@/stores/user';
import { getInventoryByModelNumber } from '@/api/inventory';
import { getCustomerList } from '@/api/customer';

// 获取用户信息
const userStore = useUserStore();
const operatorId = userStore.getUserInfo()?.id;

// 订单项数据结构
interface OrderItemForm {
  id?: number;
  uid: string; // 添加唯一标识符
  model_number: string;
  item_id: number | null;
  quantity: number | null;
  price_per_piece: number | null;
  subtotal: number | null;
  original_subtotal: number | null;
  price_difference: number | null;
  total_pieces?: number;
  source_warehouse?: number;
  category: number;
  specification?: string;
  surface?: number;
}

// 订单主表单数据
const orderForm = ref({
  customer_phone: '',
  operator_id: operatorId,
  order_remark: '',
  total_amount: 0,
});

// 客户查询相关
interface CustomerItem {
  value: string;
  link: string;
  id: number;
  nickname: string;
  phone: string;
  level_name?: string;
  is_registered: boolean;
}

const customerList = ref<CustomerItem[]>([]);
const selectedCustomer = ref<CustomerItem | null>(null);
const phoneBookVisible = ref(false);
const phoneBookLoading = ref(false);
const phoneBookList = ref<CustomerItem[]>([]);
const phoneBookSearch = ref('');

// 查询客户是否已注册（电话谱匹配）
const querySearchAsync = async (queryString: string, cb: (arg: any) => void) => {
  if (!queryString) {
    selectedCustomer.value = null;
    cb([]);
    return;
  }
  
  try {
    const res = await getCustomerList({ phone: queryString });
    if (res.data.code === 200 && res.data.data) {
      const results = res.data.data.map((item: any) => ({
        value: item.phone,
        link: item.id,
        id: item.id,
        nickname: item.nickname || '未设置昵称',
        phone: item.phone,
        level_name: item.level_name || '普通会员',
        is_registered: true
      }));
      cb(results);
    } else {
      cb([]);
    }
  } catch (e) {
    console.error(e);
    cb([]);
  }
};

// 选择已注册客户
const handleSelect = (item: CustomerItem) => {
  selectedCustomer.value = item;
  orderForm.value.customer_phone = item.value;
};

// 清除已选客户
const handleClearCustomer = () => {
  selectedCustomer.value = null;
};

// 打开电话谱对话框
const openPhoneBook = async () => {
  phoneBookVisible.value = true;
  phoneBookLoading.value = true;
  phoneBookSearch.value = '';
  
  try {
    // 获取所有客户列表
    const res = await getCustomerList({ size: 100 });
    if (res.data.code === 200 && res.data.data) {
      // 处理分页数据结构
      const records = res.data.data.records || res.data.data;
      phoneBookList.value = records.map((item: any) => ({
        value: item.phone,
        link: item.id,
        id: item.id,
        nickname: item.nickname || '未设置昵称',
        phone: item.phone,
        level_name: item.level_name || '普通会员',
        is_registered: true
      }));
    }
  } catch (e) {
    console.error('获取客户列表失败:', e);
    ElMessage.error('获取客户列表失败');
  } finally {
    phoneBookLoading.value = false;
  }
};

// 从电话谱选择客户
const selectFromPhoneBook = (customer: CustomerItem) => {
  selectedCustomer.value = customer;
  orderForm.value.customer_phone = customer.phone;
  phoneBookVisible.value = false;
  ElMessage.success(`已选择客户: ${customer.nickname}`);
};

// 电话谱搜索过滤
const filteredPhoneBookList = computed(() => {
  if (!phoneBookSearch.value) return phoneBookList.value;
  const keyword = phoneBookSearch.value.toLowerCase();
  return phoneBookList.value.filter(item => 
    item.phone.includes(keyword) || 
    item.nickname.toLowerCase().includes(keyword)
  );
});

// 生成唯一ID的函数
const generateUID = () => `item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// 订单项列表
const orderItems = ref<OrderItemForm[]>([
  {
    uid: generateUID(),
    model_number: '',
    item_id: null,
    quantity: null,
    price_per_piece: null,
    subtotal: null,
    original_subtotal: null,
    price_difference: null,
    category: 0
  }
]);

// 计算总金额
const calculateTotal = computed(() => {
  return orderItems.value.reduce((sum, item) => {
    return sum + (item.subtotal || 0);
  }, 0);
});

// 更新订单项小计金额
const updateSubtotal = (index: number) => {
  const item = orderItems.value[index];
  if (item.quantity && item.price_per_piece) {
    // 计算小计
    const calculatedSubtotal = Number((item.quantity * item.price_per_piece).toFixed(2));
    item.subtotal = calculatedSubtotal;
    item.original_subtotal = calculatedSubtotal;
    // 重置差价
    item.price_difference = 0;
    // 自动更新总金额
    orderForm.value.total_amount = calculateTotal.value;
  }
};

// 监听小计变化
const handleSubtotalChange = (index: number) => {
  const item = orderItems.value[index];
  if (item.subtotal !== null && item.original_subtotal !== null) {
    // 只有当手动输入的小计与原始计算的小计不同时，才计算并显示差价
    if (item.subtotal !== item.original_subtotal) {
      item.price_difference = Number((item.subtotal - item.original_subtotal).toFixed(2));
    } else {
      item.price_difference = 0;
    }
    // 更新总金额
    orderForm.value.total_amount = calculateTotal.value;
  }
};

// 添加新的订单项
const addOrderItem = () => {
  orderItems.value.push({
    uid: generateUID(),
    model_number: '',
    item_id: null,
    quantity: null,
    price_per_piece: null,
    subtotal: null,
    original_subtotal: null,
    price_difference: null,
    category: 0
  });
};

// 移除订单项
const removeOrderItem = (index: number) => {
  if (orderItems.value.length > 1) {
    orderItems.value.splice(index, 1);
    // 更新总金额
    orderForm.value.total_amount = calculateTotal.value;
  } else {
    ElMessage.warning('订单至少需要一项商品');
  }
};

// 监听产品型号变化
const handleModelNumberChange = async (index: number) => {
  const item = orderItems.value[index];
  if (item.model_number) {
    try {
      const result = await getInventoryByModelNumber(item.model_number);
      if (result.data.code === 200 && result.data.data) {
        const inventoryData = result.data.data;
        // 根据新接口返回的数据结构进行映射
        item.item_id = inventoryData.id; // 使用id而不是item_id
        item.total_pieces = inventoryData.total_amount; // 使用total_amount而不是total_pieces
        item.source_warehouse = 1; // 默认设置为1号仓库
        
        // 注意：新接口不返回category、specification、surface等信息
        // 这些字段需要用户手动填写或通过其他方式获取
        ElMessage.success('已自动填充商品ID和库存数量，请手动选择商品分类');
      } else {
        ElMessage.warning('未找到对应的库存信息');
        item.item_id = null;
        item.total_pieces = undefined;
        item.source_warehouse = undefined;
      }
    } catch (error) {
      console.error('获取库存信息失败:', error);
      ElMessage.error('获取库存信息失败');
      item.item_id = null;
      item.total_pieces = undefined;
      item.source_warehouse = undefined;
    }
  }
};

// 提交订单
const submitOrder = async () => {
  try {
    // 验证操作员ID
    if (!operatorId) {
      ElMessage.error('未获取到操作员信息，请重新登录');
      return;
    }

    // 验证主表单
    if (!orderForm.value.customer_phone) {
      ElMessage.error('请填写客户手机号');
      return;
    }

    // 验证手机号格式
    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!phoneRegex.test(orderForm.value.customer_phone)) {
      ElMessage.error('请输入有效的11位手机号码');
      return;
    }

    // 验证订单项
    for (let i = 0; i < orderItems.value.length; i++) {
      const item = orderItems.value[i];
      if (!item.model_number || !item.item_id || !item.quantity || !item.price_per_piece) {
        ElMessage.error(`请完善第${i + 1}项商品的信息`);
        return;
      }

      if (item.quantity <= 0) {
        ElMessage.error(`第${i + 1}项商品的数量必须大于0`);
        return;
      }

      if (item.price_per_piece <= 0) {
        ElMessage.error(`第${i + 1}项商品的单价必须大于0`);
        return;
      }

      if ([1, 2].includes(item.category)) {
        if (!item.specification) {
          ElMessage.error(`第${i + 1}项商品必须填写规格`);
          return;
        }
        if (!item.surface) {
          ElMessage.error(`第${i + 1}项商品必须选择表面处理`);
          return;
        }
      }
    }

    // 准备提交数据
    const submitData = {
      customer_phone: orderForm.value.customer_phone,
      total_price: orderForm.value.total_amount, // 使用total_price而不是total_amount
      items: orderItems.value.map(item => ({
        item_id: Number(item.item_id),
        model: item.model_number,
        amount: Number(item.quantity),
        subtotal_price: Number(item.subtotal)
      })),
      remark: orderForm.value.order_remark || undefined
    };

    // 调用API
    const response = await postOrder(submitData);
    const data = response.data;
    if (data.code === 200) {
      ElMessage.success('订单创建成功');
      resetForm();
    } else {
      throw new Error(data.message || '响应状态异常');
    }
  } catch (error) {
    console.error('Order creation failed:', error);
    ElMessage.error('订单创建失败，请稍后重试');
  }
};

// 重置表单
const resetForm = () => {
  orderForm.value = {
    customer_phone: '',
    operator_id: operatorId,
    order_remark: '',
    total_amount: 0
  };

  orderItems.value = [{
    uid: generateUID(),
    model_number: '',
    item_id: null,
    quantity: null,
    price_per_piece: null,
    subtotal: null,
    original_subtotal: null,
    price_difference: null,
    category: 0
  }];
};

// 更新产品分类选项
const categoryOptions = [
  { label: '墙砖', value: 1 },
  { label: '地砖', value: 2 },
  { label: '胶', value: 3 },
  { label: '地漏', value: 4 },
  { label: '洁具', value: 5 }
];

// 修改表单验证规则
const rules = reactive({
  // ... 其他规则保持不变
  specification: [
    { required: false, message: '请输入规格', trigger: 'blur' },
    { pattern: /^[0-9]+x[0-9]+mm$/, message: '规格格式建议为数字x数字mm，如600x600mm', trigger: 'blur' }
  ],
  surface: [
    { required: false, message: '请选择表面处理', trigger: 'change' }
  ]
});

// 动态显示规格和表面处理字段
const showSpecificationAndSurface = computed(() => {
  const item = orderItems.value[0];
  return item && [1, 2].includes(item.category);
});
</script>

<template>
  <h1>创建订单</h1>
  <hr>
  <div class="form-container">
    <el-form label-width="120px">
      <!-- 订单基本信息 -->
      <el-card class="order-card">
        <template #header>
          <div class="card-header">
            <span>订单基本信息</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户电话" required>
              <div class="phone-input-wrapper">
                <el-autocomplete
                  v-model="orderForm.customer_phone"
                  :fetch-suggestions="querySearchAsync"
                  placeholder="请输入客户手机号"
                  @select="handleSelect"
                  @clear="handleClearCustomer"
                  clearable
                  style="flex: 1"
                >
                  <template #default="{ item }">
                    <div class="customer-suggestion">
                      <div class="customer-phone">
                        <el-icon class="registered-icon"><UserFilled /></el-icon>
                        {{ item.value }}
                      </div>
                      <div class="customer-info">
                        <span class="nickname">{{ item.nickname }}</span>
                        <el-tag size="small" type="success">{{ item.level_name }}</el-tag>
                      </div>
                    </div>
                  </template>
                </el-autocomplete>
                <!-- 电话谱按钮 -->
                <el-tooltip content="打开电话谱" placement="top">
                  <el-button 
                    type="primary" 
                    :icon="Notebook" 
                    @click="openPhoneBook"
                    class="phone-book-btn"
                  />
                </el-tooltip>
              </div>
              <!-- 电话谱标志 - 显示已选客户信息 -->
              <div v-if="selectedCustomer" class="customer-badge">
                <el-tag type="success" effect="light">
                  <el-icon><UserFilled /></el-icon>
                  已注册客户
                </el-tag>
                <span class="customer-detail">
                  {{ selectedCustomer.nickname }} · {{ selectedCustomer.level_name }}
                </span>
              </div>
              <div v-else-if="orderForm.customer_phone && orderForm.customer_phone.length === 11" class="customer-badge">
                <el-tag type="info" effect="light">
                  <el-icon><User /></el-icon>
                  新客户
                </el-tag>
                <span class="new-customer-hint">该手机号尚未注册，订单创建后可在客户管理中为其注册账号</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="操作员ID">
              <el-input
                v-model.number="orderForm.operator_id"
                placeholder="系统自动获取"
                type="number"
                disabled
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="订单备注">
              <el-input
                  v-model="orderForm.order_remark"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入订单备注（可选）"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 订单商品列表 -->
      <el-card class="order-card">
        <template #header>
          <div class="card-header">
            <span>订单商品</span>
            <el-button type="primary" size="small" @click="addOrderItem">
              添加商品
            </el-button>
          </div>
        </template>

        <!-- 订单项列表 -->
        <div
            v-for="(item, index) in orderItems"
            :key="item.uid"
            class="order-item"
        >
          <div class="order-item-header">
            <h3>商品 #{{ index + 1 }}</h3>
            <el-button
                v-if="orderItems.length > 1"
                type="danger"
                size="small"
                @click="removeOrderItem(index)"
            >
              移除
            </el-button>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="产品型号" required>
                <el-input 
                  v-model="item.model_number" 
                  placeholder="请输入产品型号"
                  @change="handleModelNumberChange(index)" 
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="库存商品ID" required>
                <el-input
                  v-model.number="item.item_id"
                  placeholder="自动获取"
                  type="number"
                  disabled
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="现有库存">
                <el-input
                  v-model.number="item.total_pieces"
                  placeholder="自动获取"
                  type="number"
                  disabled
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="数量" required>
                <el-input
                    v-model.number="item.quantity"
                    placeholder="请输入购买数量"
                    type="number"
                    :min="1"
                    @input="updateSubtotal(index)"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="单价" required>
                <el-input
                    v-model.number="item.price_per_piece"
                    placeholder="请输入单价"
                    type="number"
                    :min="0"
                    :step="0.01"
                    @input="updateSubtotal(index)"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="小计">
                <el-input
                    v-model.number="item.subtotal"
                    placeholder="小计金额"
                    type="number"
                    :min="0"
                    :step="0.01"
                    @input="handleSubtotalChange(index)"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row v-if="item.price_difference !== null">
            <el-col :span="24" class="text-right">
              <span :class="{ 
                'price-difference': true,
                'positive': item.price_difference > 0,
                'negative': item.price_difference < 0
              }">
                差价: {{ item.price_difference > 0 ? '+' : '' }}{{ item.price_difference }} 元
              </span>
            </el-col>
          </el-row>
        </div>

        <!-- 订单总计 -->
        <el-divider />
        <el-row :gutter="20">
          <el-col :span="24" class="text-right">
            <h3>订单总金额: {{ orderForm.total_amount.toFixed(2) }} 元</h3>
          </el-col>
        </el-row>
      </el-card>

      <!-- 提交按钮 -->
      <div class="form-actions">
        <el-button type="primary" @click="submitOrder">提交订单</el-button>
        <el-button @click="resetForm">重置</el-button>
      </div>
    </el-form>

    <!-- 电话谱对话框 -->
    <el-dialog
      v-model="phoneBookVisible"
      title="📞 客户电话谱"
      width="600px"
      :close-on-click-modal="false"
    >
      <!-- 搜索框 -->
      <div class="phone-book-search">
        <el-input
          v-model="phoneBookSearch"
          placeholder="搜索手机号或昵称..."
          :prefix-icon="Search"
          clearable
        />
      </div>

      <!-- 客户列表 -->
      <div v-loading="phoneBookLoading" class="phone-book-list">
        <div v-if="filteredPhoneBookList.length === 0" class="phone-book-empty">
          <el-empty description="暂无客户数据" />
        </div>
        <div
          v-for="customer in filteredPhoneBookList"
          :key="customer.id"
          class="phone-book-item"
          @click="selectFromPhoneBook(customer)"
        >
          <div class="phone-book-avatar">
            <el-icon :size="24"><UserFilled /></el-icon>
          </div>
          <div class="phone-book-info">
            <div class="phone-book-name">{{ customer.nickname }}</div>
            <div class="phone-book-phone">{{ customer.phone }}</div>
          </div>
          <div class="phone-book-level">
            <el-tag size="small" type="success">{{ customer.level_name }}</el-tag>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="phoneBookVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.form-container {
  padding: 20px;
  margin-left: auto;
  margin-right: auto;
  max-width: 1000px;
}

.order-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
  background-color: #f9f9f9;
}

.order-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.order-item-header h3 {
  margin: 0;
}

.el-form-item {
  margin-bottom: 15px;
}

.text-right {
  text-align: right;
}

.form-actions {
  margin-top: 25px;
  text-align: center;
}

.el-divider {
  margin: 15px 0;
}

.price-difference {
  font-size: 14px;
  margin-right: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

/* 电话谱样式 */
.customer-suggestion {
  display: flex;
  flex-direction: column;
  padding: 5px 0;
}

.customer-phone {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: #303133;
}

.registered-icon {
  color: #67C23A;
  margin-right: 6px;
}

.customer-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.customer-info .nickname {
  color: #606266;
  font-size: 12px;
}

.customer-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.customer-badge .el-tag .el-icon {
  margin-right: 4px;
}

.customer-detail {
  color: #606266;
  font-size: 13px;
}

.new-customer-hint {
  color: #909399;
  font-size: 12px;
}

/* 电话输入框包装器 */
.phone-input-wrapper {
  display: flex;
  gap: 8px;
  width: 100%;
}

.phone-book-btn {
  flex-shrink: 0;
}

/* 电话谱对话框样式 */
.phone-book-search {
  margin-bottom: 15px;
}

.phone-book-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.phone-book-empty {
  padding: 40px 0;
}

.phone-book-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}

.phone-book-item:last-child {
  border-bottom: none;
}

.phone-book-item:hover {
  background-color: #ecf5ff;
}

.phone-book-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 12px;
  flex-shrink: 0;
}

.phone-book-info {
  flex: 1;
  min-width: 0;
}

.phone-book-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
  margin-bottom: 4px;
}

.phone-book-phone {
  color: #606266;
  font-size: 13px;
}

.phone-book-level {
  flex-shrink: 0;
  margin-left: 10px;
}
</style>