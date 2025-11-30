<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getInventoryLogsCompat, updateInventoryLogCompat, deleteInventoryLog } from '@/api/inventoryLog';
import { useUserStore } from '@/stores/user';
import type { InventoryLog, LogQueryParams, InventoryLogChangeRequest } from '@/types/interfaces';

// Store inventory records and search state
const inventoryRecords = ref<InventoryLog[]>([]);
const filteredRecords = ref<InventoryLog[]>([]);
const searchDateRange = ref<[Date, Date] | []>([]);
const total = ref(0); // Total records
const page = ref(1); // Current page
const size = ref(10); // Page size

// Dialog control
const editDialogVisible = ref(false);
const editForm = ref<InventoryLog>({
  id: 0,
  inventory_item_id: 0,
  operation_type: 1, // 固定为入库
  quantity_change: 0,
  operator_id: 0,
  source_warehouse: null,
  target_warehouse: null,
  remark: '',
  create_time: '',
  update_time: '',
});

// Define picker options for el-date-picker
const pickerOptions = {
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
const sortInventoryRecords = (list: InventoryLog[]) => {
  return [...list].sort((a, b) => {
    const idA = a.id || 0;
    const idB = b.id || 0;
    return idB - idA; // 降序排序
  });
};

// Fetch inventory records from API（限定 operation_type=1）
const fetchInventoryRecords = async () => {
  try {
    const params: LogQueryParams = {
      current: page.value,
      size: size.value,
      operation_type: 1, // 限定为入库记录
      sort: 'id',
      order: 'desc'
    };
    if (searchDateRange.value.length === 2) {
      const [startDate, endDate] = searchDateRange.value;
      params.start_time = new Date(startDate).toISOString().slice(0, 19).replace('T', ' ');
      params.end_time = new Date(endDate).toISOString().slice(0, 19).replace('T', ' ');
    }

    const response: any = await getInventoryLogsCompat(params);
    if (response.data.code === 200 && response.data.data?.records) {
      // 对数据进行排序
      const sortedRecords = sortInventoryRecords(response.data.data.records);
      inventoryRecords.value = sortedRecords;
      filteredRecords.value = sortedRecords;
      total.value = response.data.data.total || 0;
    } else {
      inventoryRecords.value = [];
      filteredRecords.value = [];
      total.value = 0;
      ElMessage.warning('获取数据失败');
    }
  } catch (error) {
    console.error('Failed to fetch inventory records:', error);
    inventoryRecords.value = [];
    filteredRecords.value = [];
    total.value = 0;
    ElMessage.error('无法获取入库记录数据');
  }
};

// Load data on mount
onMounted(() => {
  fetchInventoryRecords();
});

// Edit record
const handleEdit = (row: InventoryLog) => {
  editForm.value = { ...row };
  // 设置操作人ID为当前用户ID
  editForm.value.operator_id = operatorId || 0;
  editDialogVisible.value = true;
};

const saveEdit = async () => {
  try {
    // 根据接口文档，使用正确的参数结构
    const updateData: InventoryLogChangeRequest = {
      id: editForm.value.id!,
      inventory_item_id: editForm.value.inventory_item_id,
      operator_id: operatorId || 0,
      operation_type: 1, // 入库记录页面固定为1（入库）
      source_warehouse: editForm.value.source_warehouse,
      target_warehouse: editForm.value.target_warehouse,
      quantity_change: editForm.value.quantity_change,
      remark: editForm.value.remark,
    };

    // 根据接口文档，更新调用需要传changeType=0表示修改操作
    const response = await updateInventoryLogCompat(updateData, 0);

    if (response.data.code === 200) {
      ElMessage.success('编辑成功');
      editDialogVisible.value = false;
      await fetchInventoryRecords();
    } else {
      throw new Error(response.data.message || '响应状态异常');
    }
  } catch (error) {
    console.error('Failed to update record:', error);
    ElMessage.error('编辑失败，请稍后重试');
  }
};

// Delete record
const handleDelete = async (row: InventoryLog) => {
  try {
    await ElMessageBox.confirm('确定删除此入库记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    const response = await deleteInventoryLog(row.id!);
    if (response.data.code === 200) {
      ElMessage.success('删除成功');
      await fetchInventoryRecords();
    } else {
      throw new Error(response.data.message || '响应状态异常');
    }
  } catch (error) {
    if ((error as any).message !== 'cancel') {
      console.error('Failed to delete record:', error);
      ElMessage.error('删除失败，请稍后重试');
    }
  }
};

// Clear filter and refresh
const clearFilter = () => {
  searchDateRange.value = [];
  page.value = 1; // 重置到第一页
  fetchInventoryRecords();
};

// Pagination handlers
const handlePageChange = (newPage: number) => {
  page.value = newPage;
  fetchInventoryRecords();
};

const handleSizeChange = (newSize: number) => {
  size.value = newSize;
  page.value = 1; // 重置到第一页
  fetchInventoryRecords();
};
</script>

<template>
  <h1>入库记录</h1>
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
              @change="fetchInventoryRecords"
          />
        </el-form-item>
      </el-col>
      <el-col :span="4">
        <el-button type="default" @click="clearFilter">清除筛选</el-button>
      </el-col>
    </el-row>

    <!-- Records Table -->
    <el-table
        :data="filteredRecords"
        style="width: 100%"
        border
        max-height="600"
    >
      <el-table-column prop="id" label="记录ID" width="80" />
      <el-table-column prop="inventory_item_id" label="库存项ID" width="100" />
      <el-table-column prop="quantity_change" label="入库数量" width="120">
        <template #default="{ row }">
          {{ row.quantity_change }} 片
        </template>
      </el-table-column>
      <el-table-column prop="target_warehouse" label="目标仓库" width="100" />
      <el-table-column prop="remark" label="备注" min-width="150" />
      <el-table-column prop="create_time" label="创建时间" width="160" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button 
            type="primary" 
            size="small" 
            @click="handleEdit(row)"
            :disabled="!isAdmin"
          >
            编辑
          </el-button>
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

    <!-- Edit Dialog -->
    <el-dialog
        v-model="editDialogVisible"
        title="编辑入库记录"
        width="50%"
        :close-on-click-modal="false"
    >
      <el-form label-width="120px">
        <el-form-item label="库存项ID">
          <el-input v-model="editForm.inventory_item_id" disabled />
        </el-form-item>
        <el-form-item label="入库数量">
          <el-input-number v-model="editForm.quantity_change" :min="1" />
        </el-form-item>
        <el-form-item label="目标仓库">
          <el-input-number v-model="editForm.target_warehouse" :min="1" :max="5" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>
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