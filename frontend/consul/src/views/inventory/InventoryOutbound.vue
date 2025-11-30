<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getInventoryLogsCompat, deleteInventoryLog } from '@/api/inventoryLog';
import { useUserStore } from '@/stores/user';
import type { InventoryLog, LogQueryParams } from '@/types/interfaces';

// Store outbound inventory records and search state
const outboundRecords = ref<InventoryLog[]>([]);
const total = ref(0); // Total records
const page = ref(1); // Current page
const size = ref(10); // Page size
const searchDateRange = ref<[Date, Date] | []>([]);

// Dialog control removed for outbound records

// Define picker options for el-date-picker
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
  disabledDate(time: Date) {
    const now = new Date();
    const tenYearsAgo = now.getFullYear() - 10;
    const tenYearsLater = now.getFullYear() + 10;
    return time.getFullYear() < tenYearsAgo || time.getFullYear() > tenYearsLater;
  },
};

// 获取用户信息
const userStore = useUserStore();
const operatorId = userStore.getUserInfo()?.id;

// 检查是否为admin角色
const isAdmin = computed(() => {
  return userStore.isAdmin();
});

// 添加排序方法
const sortOutboundRecords = (list: InventoryLog[]) => {
  return [...list].sort((a, b) => {
    const idA = a.id || 0;
    const idB = b.id || 0;
    return idB - idA; // 降序排序
  });
};

// Fetch outbound inventory records from API（限定 operation_type=2）
const fetchOutboundRecords = async () => {
  try {
    const params: LogQueryParams = {
      current: page.value,
      size: size.value,
      operation_type: 2, // 限定为出库记录
      sort: 'id',
      order: 'desc'
    };
    if (searchDateRange.value.length === 2) {
      const [startDate, endDate] = searchDateRange.value;
      params.start_time = new Date(startDate).toISOString().slice(0, 19).replace('T', ' ');
      params.end_time = new Date(endDate).toISOString().slice(0, 19).replace('T', ' ');
    }

    const response: any = await getInventoryLogsCompat(params);
    if (response.data && response.data.code === 200) {
      // 对数据进行排序
      outboundRecords.value = sortOutboundRecords(response.data.data.records || []);
      total.value = response.data.data.total || 0;
    } else {
      ElMessage.warning('获取数据失败：' + (response.data?.message || '未知错误'));
      outboundRecords.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('Failed to fetch outbound records:', error);
    ElMessage.error('获取出库记录失败，请检查网络连接或联系管理员');
    outboundRecords.value = [];
    total.value = 0;
  }
};

// Load data on mount
onMounted(() => {
  fetchOutboundRecords();
});

// Edit functionality removed for outbound records

// Delete record
const handleDelete = async (row: InventoryLog) => {
  try {
    await ElMessageBox.confirm('确定删除此出库记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    const response = await deleteInventoryLog(row.id!);
    if (response.data && response.data.code === 200) {
      ElMessage.success('删除成功');
      await fetchOutboundRecords();
    } else {
      throw new Error(response.data?.message || '删除失败');
    }
  } catch (error) {
    if ((error as any).message !== 'cancel') {
      console.error('Failed to delete outbound record:', error);
      ElMessage.error('删除失败：' + ((error as Error).message || '未知错误'));
    }
  }
};

// Pagination handlers
const handlePageChange = (newPage: number) => {
  page.value = newPage;
  fetchOutboundRecords();
};

const handleSizeChange = (newSize: number) => {
  size.value = newSize;
  page.value = 1; // 重置到第一页
  fetchOutboundRecords();
};

// Clear filter and refresh
const clearFilter = () => {
  searchDateRange.value = [];
  page.value = 1; // 重置到第一页
  fetchOutboundRecords();
};
</script>

<template>
  <h1>出库记录</h1>
  <hr>
  <div class="records-container">
    <!-- Search Section -->
    <el-row :gutter="20" class="search-section">
      <el-col :span="8">
        <el-form-item label="按日期筛选">
          <el-date-picker
              v-model="searchDateRange"
              type="daterange"
              unlink-panels
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :picker-options="pickerOptions"
              @change="fetchOutboundRecords"
          />
        </el-form-item>
      </el-col>
      <el-col :span="4">
        <el-button type="default" @click="clearFilter">清除筛选</el-button>
      </el-col>
    </el-row>

    <!-- Records Table -->
    <el-table
        :data="outboundRecords"
        style="width: 100%"
        border
        max-height="600"
    >
      <el-table-column prop="id" label="记录ID" width="80" />
      <el-table-column prop="inventory_item_id" label="库存项ID" width="100" />
      <el-table-column prop="quantity_change" label="出库数量" width="120">
        <template #default="{ row }">
          {{ row.quantity_change }} 片
        </template>
      </el-table-column>
      <el-table-column prop="source_warehouse" label="源仓库" width="100" />
      <el-table-column prop="remark" label="备注" min-width="150" />
      <el-table-column prop="create_time" label="创建时间" width="160" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button 
            type="danger" 
            size="small" 
            @click="handleDelete(row)"
            :disabled="!isAdmin"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination">
      <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
      />
    </div>

    <!-- Edit Dialog removed for outbound records -->
  </div>
</template>

<style scoped>
.records-container {
  padding: 20px;
}

.search-section {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: bold;
}

:deep(.el-pagination) {
  justify-content: center;
}
</style>