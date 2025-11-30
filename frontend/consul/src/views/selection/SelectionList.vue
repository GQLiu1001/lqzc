<template>
  <div class="selection-list-container">
    <div class="header-section">
      <h2 class="page-title">选品单管理</h2>
      
      <!-- 搜索区域 -->
      <div class="search-form">
        <el-form :inline="true" :model="searchForm" class="demo-form-inline">
          <el-form-item label="选品单号">
            <el-input v-model="searchForm.selection_no" placeholder="请输入选品单号" clearable />
          </el-form-item>
          <el-form-item label="客户电话">
            <el-input v-model="searchForm.customer_phone" placeholder="请输入客户电话" clearable />
          </el-form-item>
          <el-form-item label="处理状态">
            <el-select v-model="searchForm.status" placeholder="选择状态" style="width: 120px">
              <el-option label="全部状态" :value="undefined" />
              <el-option label="待跟进" :value="0" />
              <el-option label="已联系" :value="1" />
              <el-option label="已到店" :value="2" />
              <el-option label="已失效" :value="3" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchSelectionLists">搜索</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 表格区域 -->
    <div class="table-section">
      <el-table :data="tableData" style="width: 100%" v-loading="loading">
        <el-table-column prop="selection_no" label="选品单号" width="160" />
        <el-table-column prop="customer_phone" label="客户电话" width="130" />
        <el-table-column prop="status" label="处理状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="delivery_address" label="派送地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="viewDetail(scope.row)">查看详情</el-button>
            <el-button link type="warning" @click="editSelection(scope.row)">编辑</el-button>
                         <el-dropdown @command="(command: string) => handleStatusChange(scope.row, command)">
              <el-button link type="info">
                状态变更<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="0" :disabled="scope.row.status === 0">待跟进</el-dropdown-item>
                  <el-dropdown-item command="1" :disabled="scope.row.status === 1">已联系</el-dropdown-item>
                  <el-dropdown-item command="2" :disabled="scope.row.status === 2">已到店</el-dropdown-item>
                  <el-dropdown-item command="3" :disabled="scope.row.status === 3">已失效</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button 
              link 
              type="success" 
              @click="showDispatchDialog(scope.row)"
              :disabled="scope.row.status === 3"
            >
              派单
            </el-button>
            <el-button link type="danger" @click="deleteSelection(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-section">
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

    <!-- 编辑选品单对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑选品单"
      width="600px"
      :before-close="handleEditClose"
    >
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="客户电话" prop="customer_phone">
          <el-input v-model="editForm.customer_phone" placeholder="请输入客户电话" />
        </el-form-item>
        <el-form-item label="派送地址" prop="delivery_address">
          <el-input 
            v-model="editForm.delivery_address" 
            type="textarea" 
            :rows="3"
            placeholder="请输入派送地址" 
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input 
            v-model="editForm.remark" 
            type="textarea" 
            :rows="4"
            placeholder="请输入备注信息" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit" :loading="editLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 派单对话框 -->
    <el-dialog
      v-model="dispatchDialogVisible"
      title="订单派送"
      width="500px"
      :before-close="handleDispatchClose"
    >
      <div class="dispatch-info">
        <p><strong>选品单号：</strong>{{ currentSelection?.selection_no }}</p>
        <p><strong>客户电话：</strong>{{ currentSelection?.customer_phone }}</p>
        <p><strong>派送地址：</strong>{{ currentSelection?.delivery_address }}</p>
      </div>
      <el-alert
        title="提示"
        description="派单后将创建正式订单，并进入配送流程。请确认信息无误后操作。"
        type="warning"
        :closable="false"
        style="margin: 20px 0;"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dispatchDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDispatch" :loading="dispatchLoading">确认派单</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <SelectionDetail 
      :visible="detailDialogVisible" 
      :selection-id="currentSelectionId"
      @close="detailDialogVisible = false"
      @refresh="fetchSelectionLists"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowDown } from '@element-plus/icons-vue';
import {
  getSelectionLists,
  updateSelectionStatus,
  deleteSelectionList,
  updateSelectionList,
  dispatchSelectionOrder
} from '@/api/selection';
import type { 
  SelectionListItem, 
  SelectionListQueryParams, 
  SelectionListChangeReq 
} from '@/types/interfaces';
import SelectionDetail from '@/views/selection/SelectionDetail.vue';

// 响应式数据
const tableData = ref<SelectionListItem[]>([]);
const loading = ref(false);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// 搜索表单
const searchForm = reactive<SelectionListQueryParams>({
  selection_no: '',
  customer_phone: '',
  status: undefined,
});

// 编辑对话框
const editDialogVisible = ref(false);
const editLoading = ref(false);
const editFormRef = ref();
const editForm = reactive<SelectionListChangeReq & { id?: number }>({
  customer_phone: '',
  delivery_address: '',
  remark: '',
});

const editRules = {
  customer_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
};

// 派单对话框
const dispatchDialogVisible = ref(false);
const dispatchLoading = ref(false);
const currentSelection = ref<SelectionListItem | null>(null);

// 详情对话框
const detailDialogVisible = ref(false);
const currentSelectionId = ref<number>(0);

// 获取状态类型样式
const getStatusType = (status: number) => {
  const types = ['warning', 'info', 'success', 'danger'];
  return types[status] || 'info';
};

// 获取状态文字
const getStatusText = (status: number) => {
  const texts = ['待跟进', '已联系', '已到店', '已失效'];
  return texts[status] || '未知';
};

// 获取选品单列表
const fetchSelectionLists = async () => {
  loading.value = true;
  try {
    const params = {
      current: currentPage.value,
      size: pageSize.value,
      ...searchForm,
    };
    
    const response = await getSelectionLists(params);
    // 使用类型断言来处理axios响应结构
    const result = response as any;
    tableData.value = result.data.data.records;
    total.value = result.data.data.total;
  } catch (error) {
    console.error('获取选品单列表失败:', error);
    ElMessage.error('获取选品单列表失败');
  } finally {
    loading.value = false;
  }
};

// 搜索
const searchSelectionLists = () => {
  currentPage.value = 1;
  fetchSelectionLists();
};

// 重置搜索
const resetSearch = () => {
  Object.assign(searchForm, {
    selection_no: '',
    customer_phone: '',
    status: undefined,
  });
  currentPage.value = 1;
  fetchSelectionLists();
};

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  currentPage.value = 1;
  fetchSelectionLists();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchSelectionLists();
};

// 状态变更
const handleStatusChange = async (row: SelectionListItem, status: string) => {
  try {
    const response = await updateSelectionStatus(row.id, parseInt(status));
    const result = response as any;
    if (result.data.code === 200) {
      ElMessage.success('状态更新成功');
      fetchSelectionLists();
    } else {
      ElMessage.error(result.data.message || '状态更新失败');
    }
  } catch (error) {
    console.error('状态更新失败:', error);
    ElMessage.error('状态更新失败');
  }
};

// 查看详情
const viewDetail = (row: SelectionListItem) => {
  currentSelectionId.value = row.id;
  detailDialogVisible.value = true;
};

// 编辑选品单
const editSelection = (row: SelectionListItem) => {
  Object.assign(editForm, {
    id: row.id,
    customer_phone: row.customer_phone || '',
    delivery_address: row.delivery_address || '',
    remark: row.remark || '',
  });
  editDialogVisible.value = true;
};

// 提交编辑
const submitEdit = async () => {
  if (!editFormRef.value) return;
  
  await editFormRef.value.validate(async (valid: boolean) => {
    if (valid && editForm.id) {
      editLoading.value = true;
      try {
        const { id, ...updateData } = editForm;
        const response = await updateSelectionList(id, updateData);
        const result = response as any;
        if (result.data.code === 200) {
          ElMessage.success('更新成功');
          editDialogVisible.value = false;
          fetchSelectionLists();
        } else {
          ElMessage.error(result.data.message || '更新失败');
        }
      } catch (error) {
        console.error('更新失败:', error);
        ElMessage.error('更新失败');
      } finally {
        editLoading.value = false;
      }
    }
  });
};

// 编辑对话框关闭处理
const handleEditClose = () => {
  editFormRef.value?.resetFields();
  editDialogVisible.value = false;
};

// 显示派单对话框
const showDispatchDialog = (row: SelectionListItem) => {
  currentSelection.value = row;
  dispatchDialogVisible.value = true;
};

// 确认派单
const confirmDispatch = async () => {
  if (!currentSelection.value) return;
  
  dispatchLoading.value = true;
  try {
    const response = await dispatchSelectionOrder(currentSelection.value.id);
    const result = response as any;
    if (result.data.code === 200) {
      ElMessage.success('派单成功');
      dispatchDialogVisible.value = false;
      fetchSelectionLists();
    } else {
      ElMessage.error(result.data.message || '派单失败');
    }
  } catch (error) {
    console.error('派单失败:', error);
    ElMessage.error('派单失败');
  } finally {
    dispatchLoading.value = false;
  }
};

// 派单对话框关闭处理
const handleDispatchClose = () => {
  currentSelection.value = null;
  dispatchDialogVisible.value = false;
};

// 删除选品单
const deleteSelection = async (row: SelectionListItem) => {
  try {
    await ElMessageBox.confirm('确定要删除这个选品单吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    const response = await deleteSelectionList(row.id);
    const result = response as any;
    if (result.data.code === 200) {
      ElMessage.success('删除成功');
      fetchSelectionLists();
    } else {
      ElMessage.error(result.data.message || '删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 初始化
onMounted(() => {
  fetchSelectionLists();
});
</script>

<style scoped>
.selection-list-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #303133;
}

.search-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.table-section {
  background: white;
  border-radius: 6px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dispatch-info {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.dispatch-info p {
  margin: 8px 0;
  color: #606266;
}
</style> 