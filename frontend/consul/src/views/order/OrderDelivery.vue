<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { useUserStore } from '@/stores/user';
// 使用专门的派送系统API
import { getAvailableOrders } from '@/api/delivery';
import type { DeliveryOrder } from '@/types/interfaces';

// 添加从Order定义派生的类型，来匹配getOrders返回的订单数据
interface OrderData {
  id: number;
  order_no: string;
  customer_phone: string;
  total_amount: number;
  adjusted_amount?: number;
  order_remark?: string;
  order_create_time: string;
  order_update_time?: string;
  delivery_status?: number;
  delivery_address?: string;
  dispatch_status?: number; // 新增字段，与orderInfo表中的dispatch_status对应
  [key: string]: any; // 添加索引签名以允许其他可能的字段
}

// 扩展DeliveryOrder接口，使用snake_case字段名
interface EnhancedDeliveryOrder extends DeliveryOrder {
  order_id?: number;
  total_amount?: number;
  order_create_time?: string;
  order_update_time?: string;
}

// 获取用户信息
const userStore = useUserStore();
const operatorId = userStore.getUserInfo()?.id;

// 表格数据
const tableData = ref<EnhancedDeliveryOrder[]>([]);
const loading = ref(false);
const total = ref(0); // 总记录数
const currentPage = ref(1); // 当前页码
const pageSize = ref(10); // 每页数量

// 搜索条件
const searchDateRange = ref<[Date, Date] | []>([]);
const searchPhone = ref('');
const searchStatus = ref<number>(0); // 添加状态搜索条件，默认为待派送(0)

// 日期选择器选项
const pickerOptions = {
  shortcuts: [
    {
      text: '最近一周',
      onClick(picker: any) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
        picker.$emit('pick', [start, end]);
      },
    },
    {
      text: '最近一个月',
      onClick(picker: any) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
        picker.$emit('pick', [start, end]);
      },
    },
    {
      text: '最近三个月',
      onClick(picker: any) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
        picker.$emit('pick', [start, end]);
      },
    },
  ],
};



// 系统状态
const isDeliverySystemReady = ref(false);
const systemErrorMessage = ref('');

// 派送状态映射
const deliveryStatusMap = {
  0: { text: '待派送', type: 'info' },
  1: { text: '待接单', type: 'warning' },
  2: { text: '派送中', type: 'primary' },
  3: { text: '已完成', type: 'success' }
};

// 状态选项列表（用于下拉选择器）
const statusOptions = [
  { label: '全部状态', value: -1 },
  { label: '待派送', value: 0 },
  { label: '待接单', value: 1 },
  { label: '派送中', value: 2 },
  { label: '已完成', value: 3 }
];

// 获取派送状态文本
const getDeliveryStatusText = (status: number | undefined) => {
  if (status === undefined) return '未分配';
  return deliveryStatusMap[status as keyof typeof deliveryStatusMap]?.text || '未知状态';
};

// 获取派送状态类型（用于标签颜色）
const getDeliveryStatusType = (status: number | undefined) => {
  if (status === undefined) return 'info';
  return deliveryStatusMap[status as keyof typeof deliveryStatusMap]?.type || '';
};



// 格式化日期
const formatDate = (date: Date, isEndDate = false) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  if (isEndDate) {
    return `${year}-${month}-${day} 23:59:59`;
  }
  return `${year}-${month}-${day} 00:00:00`;
};

// 重置搜索条件
const resetSearch = () => {
  searchDateRange.value = [];
  searchPhone.value = '';
  searchStatus.value = 0; // 重置状态为待派送
  currentPage.value = 1;
  loadPendingOrders();
};

// 分页处理函数
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  currentPage.value = 1;
  loadPendingOrders();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  loadPendingOrders();
};

// 状态筛选变化处理
const handleStatusChange = (value: number) => {

  
  // 重置分页并重新加载数据
  currentPage.value = 1;
  loadPendingOrders();
};

// 加载待派送订单列表
const loadPendingOrders = async () => {
  loading.value = true;
  systemErrorMessage.value = '';
  
  try {
    // 构建搜索参数
    const searchParams: any = {};

    // 添加手机号筛选
    if (searchPhone.value.trim()) {
      searchParams.customerPhone = searchPhone.value.trim();
    }

    // 添加日期筛选
    if (searchDateRange.value && searchDateRange.value.length === 2) {
      const [startDate, endDate] = searchDateRange.value;
      if (startDate && endDate) {
        searchParams.startTime = formatDate(startDate);
        searchParams.endTime = formatDate(endDate, true);
      }
    }

    // 使用派送系统的API - 根据选择的状态查询订单
    const queryStatus = searchStatus.value === -1 ? 0 : searchStatus.value; // 如果选择"全部状态"，默认查询待派送
  
    
    const response = await getAvailableOrders(queryStatus, currentPage.value, pageSize.value, searchParams);
    
    if (response && response.data && (response as any).data.code === 200) {
      // 设置派送系统就绪标志
      isDeliverySystemReady.value = true;
      
      // 解析返回的派送订单数据
      const responseData = (response as any).data.data;
      
      // 根据后端返回格式，应该是分页结构：{total, current, size, records}
      if (responseData && responseData.records && Array.isArray(responseData.records)) {

        // 处理分页数据结构
        const newRecords = responseData.records.map((order: any) => {
          
          return {
          id: order.id || order.order_no, // 使用order_no作为id的备选
            order_no: order.order_no,
            customer_phone: order.customer_phone,
            delivery_address: order.delivery_address || '',
            // 使用查询状态作为显示状态，因为后端按状态查询返回的都是该状态的订单
            delivery_status: order.delivery_status !== undefined ? order.delivery_status : queryStatus,
            delivery_fee: order.delivery_fee,
            goods_weight: order.goods_weight,
            delivery_note: order.remark || '', // 使用remark字段作为配送备注
            driver_id: order.driver_id,
            create_time: order.create_time,
            update_time: order.update_time
          };
        });
        
        
        // 标准分页：直接替换数据
          tableData.value = newRecords;
        
        // 设置总记录数
        total.value = responseData.total || 0;
      } else {
          tableData.value = [];
        total.value = 0;
      }
    } else {
      ElMessage.error((response as any)?.data?.message || '获取派送订单列表失败');
        tableData.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('获取派送订单列表失败:', error);
    isDeliverySystemReady.value = false;
    systemErrorMessage.value = '派送系统未就绪，请稍后再试';
      tableData.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};



// 格式化日期时间
const formatDateTime = (dateTimeStr: string | undefined) => {
  if (!dateTimeStr) return '-';
  return new Date(dateTimeStr).toLocaleString();
};

onMounted(() => {
  loadPendingOrders();
});
</script>

<template>
  <div class="order-delivery-container">
    <h1>订单派送监控</h1>
    <hr>
    
    <!-- 搜索区域 -->
    <el-card class="search-section">
      <el-form :inline="true" @submit.prevent="loadPendingOrders">
        <el-form-item label="按日期筛选">
          <el-date-picker
            v-model="searchDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :picker-options="pickerOptions"
          />
        </el-form-item>
        <el-form-item label="按手机号筛选">
          <el-input
            v-model="searchPhone"
            placeholder="输入客户手机号"
            clearable
          />
        </el-form-item>
        <el-form-item label="按状态筛选">
          <el-select
            v-model="searchStatus"
            placeholder="选择状态"
            style="width: 150px"
            @change="handleStatusChange"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPendingOrders">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 系统未就绪提示 -->
    <el-alert
      v-if="!isDeliverySystemReady && systemErrorMessage"
      :title="systemErrorMessage"
      type="warning"
      :closable="false"
      show-icon
      class="system-alert"
    >
      <template #default>
        <p>派送系统后端服务未就绪，请检查连接或联系系统管理员。</p>
        <p>目前只能通过订单管理页面的派送按钮发起派送请求，暂时无法在本页面查看派送状态。</p>
      </template>
    </el-alert>
    
    <!-- 订单列表 -->
    <el-table
      :data="tableData"
      style="width: 100%"
      v-loading="loading"
      border
      stripe
      highlight-current-row
      header-cell-class-name="table-header"
    >
      <el-table-column prop="order_no" label="订单编号" width="180" align="center" />
      <el-table-column prop="customer_phone" label="客户手机号" width="150" align="center" />
      <el-table-column prop="delivery_fee" label="配送费" width="100" align="center">
        <template #default="{ row }">
          {{ row.delivery_fee ? row.delivery_fee.toFixed(2) + ' 元' : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="goods_weight" label="货物吨数" width="100" align="center">
        <template #default="{ row }">
          {{ row.goods_weight ? row.goods_weight.toFixed(1) + ' 吨' : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="delivery_status" label="派送状态" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getDeliveryStatusType(row.delivery_status)">
            {{ getDeliveryStatusText(row.delivery_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="180" align="center">
        <template #default="{ row }">
          {{ formatDateTime(row.create_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="delivery_address" label="配送地址" min-width="200" :show-overflow-tooltip="true" />
    </el-table>
    
    <!-- 空数据提示 -->
    <div v-if="!loading && tableData.length === 0 && !systemErrorMessage" class="empty-data">
      <el-empty description="暂无派送订单数据" />
    </div>
    
    <!-- 分页器 -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    

  </div>
</template>

<style scoped>
.order-delivery-container {
  padding: 20px;
}

.search-section {
  margin-bottom: 20px;
  padding: 15px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 20px;
}

:deep(.el-date-editor.el-input__inner) {
  width: 350px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding: 20px 0;
}



:deep(.table-header) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: bold;
}

.system-alert {
  margin-bottom: 20px;
}

.empty-data {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style> 