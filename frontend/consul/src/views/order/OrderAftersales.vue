<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getOrderDetail } from '@/api/order';
import { createAftersale, getOrderAftersaleLogs, updateAftersaleStatus } from '@/api/aftersales';
import { useUserStore } from '@/stores/user';

// 订单项类型
interface OrderItem {
  id: number;
  order_id?: number;
  item_id: number;
  model_number: string;
  specification?: string;
  manufacturer?: string;
  quantity: number;
  price_per_piece: number;
  subtotal: number;
  adjusted_quantity?: number | null;
}

// 订单类型
interface Order {
  id: number;
  order_no: string;
  customer_phone: string;
  operator_id: number;
  operator_name?: string;
  total_amount: number;
  adjusted_amount?: number | null;
  order_remark?: string;
  order_create_time: string;
  order_update_time: string;
  aftersale_status?: number | null;
  items: OrderItem[];  // 订单包含的多个商品项
}

// 售后记录类型 - 根据SQL表结构修改
interface Aftersale {
  id?: number;
  order_id: number;
  order_item_id: number;
  aftersale_type: number | null;
  aftersale_status: number | null;
  quantity_change: number;
  amount_change: number;
  resolution_result: string;
  aftersale_operator: number;
  create_time?: string;
}

// 售后表单类型
interface AftersalePostRequest {
  order_id: number;
  aftersale_type: number;
  aftersale_status: number;
  items: [{
    order_item_id: number;
    quantity_change: number;
    amount_change: number;
  }];
  resolution_result: string;
  aftersale_operator: number;
}

// 路由相关
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 加载状态
const loading = ref(false);
const noOrderFound = ref(false);

// 当前售后订单
const order = ref<Order | null>(null);

// 售后表单 - 修改为直接对应SQL表结构
const aftersaleForm = ref<AftersalePostRequest>({
  order_id: 0,
  aftersale_type: 0,
  aftersale_status: 1, // 默认为"新建"状态
  items: [{
    order_item_id: 0,
    quantity_change: 0,
    amount_change: 0
  }],
  resolution_result: '',
  aftersale_operator: userStore.getUserInfo()?.id || 0
});

// 历史售后记录
const aftersaleLogs = ref<Aftersale[]>([]);
const aftersaleLogsLoading = ref(false);

// 选中的订单项
const selectedOrderItem = ref<OrderItem | null>(null);

// 获取订单详情
const fetchOrderDetail = async (orderId: number) => {
  loading.value = true;
  noOrderFound.value = false;
  selectedOrderItem.value = null;

  try {
    const response = await getOrderDetail(orderId);

    if (response.data.code === 200) {
      order.value = response.data.data;

      // 初始化售后表单
      aftersaleForm.value = {
        order_id: orderId,
        aftersale_type: 0,
        aftersale_status: 1, // 默认为"新建"状态
        items: [{
          order_item_id: 0,
          quantity_change: 0,
          amount_change: 0
        }],
        resolution_result: '',
        aftersale_operator: userStore.getUserInfo()?.id || 0
      };

      // 获取历史售后记录
      await fetchAftersaleLogs(orderId);
    } else {
      ElMessage.error(response.data.message || '获取订单详情失败');
      noOrderFound.value = true;
    }
  } catch (error) {
    console.error('获取订单详情失败:', error);
    ElMessage.error('获取订单详情失败');
    noOrderFound.value = true;
  } finally {
    loading.value = false;
  }
};

// 获取售后记录
const fetchAftersaleLogs = async (orderId: number) => {
  aftersaleLogsLoading.value = true;
  try {
    const response = await getOrderAftersaleLogs(orderId);
    const responseData = response.data as any;
    if (responseData.code === 200) {
      // 确保数据是数组格式
      if (responseData.data && !Array.isArray(responseData.data)) {
        // 如果是单个对象，将其转换为数组
        aftersaleLogs.value = [responseData.data];
      } else {
        aftersaleLogs.value = responseData.data || [];
      }
      } else {
      aftersaleLogs.value = [];
    }
  } catch (error) {
    console.error('获取售后记录失败:', error);
    aftersaleLogs.value = [];
  } finally {
    aftersaleLogsLoading.value = false;
  }
};

// 切换售后类型
const handleAftersaleTypeChange = () => {
  // 重置数量变化和金额变化
  aftersaleForm.value.items = [{
    order_item_id: 0,
    quantity_change: 0,
    amount_change: 0
  }];
  selectedOrderItem.value = null;
};

// 处理订单项选择
const handleItemSelected = (item: OrderItem) => {
  selectedOrderItem.value = item;
  // 重置数量变化和金额变化
  aftersaleForm.value.items = [{
    order_item_id: item.id,
    quantity_change: 0,
    amount_change: 0
  }];
};

// 更新金额变化
const updateAmountChange = () => {
  if (!selectedOrderItem.value || !aftersaleForm.value.items.length) return;

  const item = aftersaleForm.value.items[0];
  item.amount_change = Number((item.quantity_change * selectedOrderItem.value.price_per_piece).toFixed(2));
};

// 格式化日期时间
const formatDateTime = (dateTimeStr: string | undefined | null): string => {
  if (!dateTimeStr) return '';

  try {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } catch (e) {
    console.error('日期格式化错误:', e);
    return dateTimeStr; // 如果格式化失败，返回原始字符串
  }
};

// 获取售后类型文本
const getAftersaleTypeText = (type: number | null): string => {
  if (type === 1) return '买多退货退款';
  if (type === 2) return '买少补货补款';
  return '';
};

// 获取售后状态文本
const getAftersaleStatusText = (status: number | null): string => {
  if (status === 1) return '新建';
  if (status === 2) return '已解决';
  return '';
};

// 提交售后申请
const saveAftersale = async () => {
  if (!aftersaleForm.value.aftersale_type) {
    ElMessage.error('请选择售后类型');
    return;
  }

  if (!aftersaleForm.value.items.length || !aftersaleForm.value.items[0].order_item_id) {
    ElMessage.error('请选择商品项');
    return;
  }

  if (!aftersaleForm.value.aftersale_operator) {
    ElMessage.error('请输入售后处理人ID');
    return;
  }

  const item = aftersaleForm.value.items[0];
  if (item.quantity_change === 0) {
    ElMessage.error('数量变化不能为0');
    return;
  }

  // 检查数量变化的正负与售后类型是否匹配
  if (aftersaleForm.value.aftersale_type === 1 && item.quantity_change > 0) {
    ElMessage.error('买多退货退款类型下，数量变化应为负数');
    return;
  }

  if (aftersaleForm.value.aftersale_type === 2 && item.quantity_change < 0) {
    ElMessage.error('买少补货补款类型下，数量变化应为正数');
    return;
  }

  // 检查商品当前库存是否足够退货
  if (selectedOrderItem.value && aftersaleForm.value.aftersale_type === 1) {
    const currentQuantity = aftersaleForm.value.aftersale_type === 1 
        ? selectedOrderItem.value.quantity 
        : selectedOrderItem.value.quantity;

    if (currentQuantity !== undefined && Math.abs(item.quantity_change) > currentQuantity) {
      ElMessage.error(`退货数量不能超过当前库存 ${currentQuantity}`);
      return;
    }
  }

  try {
    loading.value = true;
    const response = await createAftersale(aftersaleForm.value);

    if (response.data.code === 200 || response.data.code === 201) {
      ElMessage.success('售后申请提交成功');

      // 重新获取订单详情以更新状态
      await fetchOrderDetail(aftersaleForm.value.order_id);

      // 重置表单
      aftersaleForm.value = {
        order_id: aftersaleForm.value.order_id,
        aftersale_type: 0,
        aftersale_status: 1,
        items: [{
          order_item_id: 0,
          quantity_change: 0,
          amount_change: 0
        }],
        resolution_result: '',
        aftersale_operator: userStore.getUserInfo()?.id || 0
      };
      selectedOrderItem.value = null;
    } else {
      ElMessage.error(response.data.message || '售后申请提交失败');
    }
  } catch (error) {
    console.error('售后申请提交失败:', error);
    ElMessage.error('售后申请提交失败');
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  router.push({ name: 'order-list' });
};

// 售后类型和状态映射
const aftersaleTypeMap = {
  1: '买多退货退款',
  2: '买少补货补款',
};

const aftersaleStatusMap = {
  1: '新建',
  2: '已解决'
};

// 处理已解决操作
const handleMarkAsResolved = async (log: Aftersale) => {
  // 确认是否将售后记录标记为已解决
  ElMessageBox.confirm('确定要将此售后记录标记为已解决吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 调用API更新售后状态
      const response = await updateAftersaleStatus(log.id!, 2);

      if (response.data.code === 200) {
        ElMessage.success('售后记录已成功标记为已解决');
        // 重新获取订单详情以更新状态
        await fetchOrderDetail(log.order_id);
      } else {
        ElMessage.error(response.data.message || '更新售后状态失败');
      }
    } catch (error) {
      console.error('更新售后状态失败:', error);
      ElMessage.error('更新售后状态失败');
    }
  }).catch(() => {
    // 取消操作
  });
};

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    const orderId = parseInt(newId as string);
    if (!isNaN(orderId)) {
      fetchOrderDetail(orderId);
    }
  }
}, { immediate: true });

onMounted(() => {
  // 获取URL中的订单ID
  const orderId = parseInt(route.params.id as string);
  if (!isNaN(orderId)) {
    fetchOrderDetail(orderId);
  }
});
</script>

<template>
  <div class="aftersale-page">
    <div class="page-header">
      <h1>订单售后管理</h1>
      <el-button type="primary" @click="goBack">返回订单列表</el-button>
    </div>
    <hr>

    <el-skeleton :loading="loading" animated>
      <template #template>
        <div class="skeleton-wrapper">
          <el-skeleton-item variant="p" style="width: 100%; height: 50px; margin-bottom: 20px;" />
          <el-skeleton-item variant="p" style="width: 100%; height: 100px;" />
          <el-skeleton-item variant="p" style="width: 100%; height: 300px; margin-top: 20px;" />
        </div>
      </template>

      <template #default>
        <div v-if="noOrderFound" class="no-order-found">
          <el-empty description="未找到订单信息">
            <el-button type="primary" @click="goBack">返回订单列表</el-button>
          </el-empty>
        </div>

        <div v-else-if="order" class="aftersale-container">
          <!-- 订单基本信息 -->
          <div class="aftersale-order-info">
            <div class="info-header">订单基本信息</div>
            <div class="info-content">
              <div class="info-row">
                <div class="info-item">
                  <span class="label">订单编号:</span>
                  <span class="value">{{ order.order_no }}</span>
                </div>
                <div class="info-item">
                  <span class="label">客户手机号:</span>
                  <span class="value">{{ order.customer_phone }}</span>
                </div>
              </div>
              <div class="info-row">
                <div class="info-item">
                  <span class="label">订单总金额:</span>
                  <span class="value">{{ order.total_amount.toFixed(2) }} 元</span>
                </div>
                <div class="info-item">
                  <span class="label">当前金额:</span>
                  <span class="value">{{ order.adjusted_amount ? order.adjusted_amount.toFixed(2) : order.total_amount.toFixed(2) }} 元</span>
                </div>
              </div>
              <div class="info-row">
                <div class="info-item">
                  <span class="label">售后状态:</span>
                  <span class="value">
                    <el-tag v-if="order.aftersale_status === 1 || order.aftersale_status === 2"
                            :type="order.aftersale_status === 1 ? 'warning' : 'success'">
                      {{ getAftersaleStatusText(order.aftersale_status) }}
                    </el-tag>
                    <span v-else>无</span>
                  </span>
                </div>
                <div class="info-item">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDateTime(order.order_create_time) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 售后基本信息 -->
          <div class="aftersale-basic-info">
            <div class="section-title">售后处理信息</div>
            <el-form :model="aftersaleForm" label-width="120px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="售后类型" required>
                    <el-select
                        v-model="aftersaleForm.aftersale_type"
                        placeholder="请选择售后类型"
                        @change="handleAftersaleTypeChange"
                    >
                      <el-option label="买多退货退款" :value="1" />
                      <el-option label="买少补货补款" :value="2" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="售后状态" required>
                    <el-select
                        v-model="aftersaleForm.aftersale_status"
                        placeholder="请选择售后状态"
                        :disabled="true"
                    >
                      <el-option label="新建" :value="1" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="售后处理人ID" required>
                    <el-input
                        v-model.number="aftersaleForm.aftersale_operator"
                        placeholder="请输入处理人ID"
                        type="number"
                        :disabled="true"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="处理结果说明">
                    <el-input
                        v-model="aftersaleForm.resolution_result"
                        placeholder="请输入处理结果说明(选填)"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>

          <!-- 售后商品选择 -->
          <div class="aftersale-items">
            <div class="section-title">选择需要售后的商品</div>

            <el-table :data="order.items" border style="width: 100%">
              <el-table-column type="selection" width="55">
                <template #default="{ row }">
                  <el-radio
                      v-model="aftersaleForm.items[0].order_item_id"
                      :label="row.id"
                      @change="handleItemSelected(row)"
                  >&nbsp;</el-radio>
                </template>
              </el-table-column>
              <el-table-column prop="model_number" label="产品型号" width="120" />
              <el-table-column label="原始数量" width="90">
                <template #default="{ row }">
                  {{ row.quantity }}
                </template>
              </el-table-column>
              <el-table-column label="当前数量" width="90">
                <template #default="{ row }">
                  {{ row.adjusted_quantity !== null ? row.adjusted_quantity : row.quantity }}
                </template>
              </el-table-column>
              <el-table-column label="单价" width="90">
                <template #default="{ row }">
                  {{ row.price_per_piece.toFixed(2) }} 元
                </template>
              </el-table-column>
              <el-table-column label="小计" width="120">
                <template #default="{ row }">
                  {{ row.subtotal.toFixed(2) }} 元
                </template>
              </el-table-column>
            </el-table>

            <div class="quantity-change-section" v-if="selectedOrderItem">
              <el-form :model="aftersaleForm" label-width="120px" class="mt-4">
                <el-form-item label="数量变化" required>
                  <el-input
                      v-model.number="aftersaleForm.items[0].quantity_change"
                      type="number"
                      placeholder="正数补货/负数退货"
                      @input="updateAmountChange"
                  />
                  <div class="hint mt-2">
                    <span v-if="aftersaleForm.aftersale_type === 1">请输入负数表示退货数量</span>
                    <span v-else-if="aftersaleForm.aftersale_type === 2">请输入正数表示补货数量</span>
                    <span v-else>请先选择售后类型</span>
                  </div>
                </el-form-item>
                <el-form-item label="金额变化">
                  <el-input
                      v-model.number="aftersaleForm.items[0].amount_change"
                      type="number"
                      :disabled="true"
                  />
                  <div class="hint mt-2">
                    <span :class="{'positive': aftersaleForm.items[0]?.amount_change > 0, 'negative': aftersaleForm.items[0]?.amount_change < 0}">
                      {{ aftersaleForm.items[0]?.amount_change > 0 ? '补款' : aftersaleForm.items[0]?.amount_change < 0 ? '退款' : '' }}
                      {{ Math.abs(aftersaleForm.items[0]?.amount_change || 0).toFixed(2) }} 元
                    </span>
                  </div>
                </el-form-item>
              </el-form>
            </div>

            <div class="submit-section">
              <el-button type="primary" @click="saveAftersale">提交售后申请</el-button>
            </div>
          </div>

          <!-- 历史售后记录 -->
          <div class="aftersale-history" v-if="aftersaleLogs.length > 0">
            <div class="section-title">历史售后记录</div>

            <el-table :data="aftersaleLogs" v-loading="aftersaleLogsLoading" border style="width: 100%">
              <el-table-column prop="id" label="记录ID" width="80" />
              <el-table-column prop="order_item_id" label="订单项ID" width="100" />
              <el-table-column label="售后类型" width="120">
                <template #default="{ row }">
                  <el-tag v-if="row.aftersale_type === 1 || row.aftersale_type === 2"
                          :type="row.aftersale_type === 1 ? 'danger' : 'success'">
                    {{ getAftersaleTypeText(row.aftersale_type) }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="售后状态" width="100">
                <template #default="{ row }">
                  <el-tag v-if="row.aftersale_status === 1 || row.aftersale_status === 2"
                          :type="row.aftersale_status === 1 ? 'warning' : 'success'">
                    {{ getAftersaleStatusText(row.aftersale_status) }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="数量变化" width="100">
                <template #default="{ row }">
                  <span :class="{'positive': row.quantity_change > 0, 'negative': row.quantity_change < 0}">
                    {{ row.quantity_change }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="金额变化" width="120">
                <template #default="{ row }">
                  <span :class="{'positive': row.amount_change > 0, 'negative': row.amount_change < 0}">
                    {{ row.amount_change.toFixed(2) }} 元
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="处理结果" min-width="150">
                <template #default="{ row }">
                  {{ row.resolution_result }}
                </template>
              </el-table-column>
              <el-table-column label="处理人" width="100">
                <template #default="{ row }">
                  {{ row.aftersale_operator }}
                </template>
              </el-table-column>
              <el-table-column label="创建时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.create_time) }}
                </template>
              </el-table-column>

              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <!-- 仅在状态为新建时显示已解决按钮 -->
                  <el-button
                      v-if="row.aftersale_status === 1"
                      type="success"
                      size="small"
                      @click="handleMarkAsResolved(row)"
                  >
                    标记已解决
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <el-empty v-else description="暂无售后记录" />
        </div>
      </template>
    </el-skeleton>
  </div>
</template>

<style scoped>
.aftersale-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.skeleton-wrapper {
  padding: 20px;
}

.aftersale-container {
  margin-top: 20px;
}

.aftersale-order-info {
  margin-bottom: 30px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.info-header {
  background-color: #f5f7fa;
  padding: 12px 15px;
  font-weight: bold;
  border-bottom: 1px solid #ebeef5;
}

.info-content {
  padding: 15px;
}

.info-row {
  display: flex;
  margin-bottom: 10px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-item {
  flex: 1;
  display: flex;
}

.label {
  width: 100px;
  color: #606266;
}

.value {
  flex: 1;
  color: #303133;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.aftersale-basic-info {
  margin-bottom: 30px;
}

.aftersale-items {
  margin-bottom: 30px;
}

.quantity-change-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.hint {
  font-size: 12px;
  color: #909399;
}

.mt-2 {
  margin-top: 8px;
}

.mt-4 {
  margin-top: 16px;
}

.submit-section {
  margin-top: 20px;
  text-align: right;
}

.aftersale-history {
  margin-top: 30px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}
</style>