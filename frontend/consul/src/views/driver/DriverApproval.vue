<template>
  <div class="driver-approval-container">
    <h1>司机审核</h1>
    <hr>
    
    <el-card class="driver-list-container" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="header-title">司机管理列表</span>
        </div>
      </template>
      <el-table 
        :data="driverList" 
        style="width: 100%" 
        v-loading="loading" 
        border 
        stripe
        highlight-current-row
        header-cell-class-name="table-header"
      >
        <el-table-column prop="id" label="ID" min-width="10%" align="center" />
        <el-table-column prop="name" label="司机姓名" min-width="20%" align="center" />
        <el-table-column prop="phone" label="手机号码" min-width="30%" align="center" />
        <el-table-column prop="money" label="账户余额" min-width="15%" align="center">
          <template #default="{ row }">
            <span>{{ row.money || 0 }}元</span>
          </template>
        </el-table-column>
        <el-table-column prop="auditStatus" label="状态" min-width="15%">
          <template #default="{ row }">
            <div class="tag-center">
              <el-tag v-if="row.auditStatus === 0" type="warning">待审核</el-tag>
              <el-tag v-else-if="row.auditStatus === 1" type="success">已审核</el-tag>
              <el-tag v-else-if="row.auditStatus === 2" type="danger">已拒绝</el-tag>
              <el-tag v-else type="info">未知</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="25%" fixed="right">
          <template #default="scope">
            <div class="button-row-center">
              <!-- 待审核状态下显示审核和拒绝按钮 -->
              <template v-if="scope.row.auditStatus === 0">
                <el-button
                  type="success" 
                  size="small" 
                  @click="handleApprove(scope.row)"
                >审核通过</el-button>
                <el-button
                  type="warning" 
                  size="small" 
                  @click="handleReject(scope.row)"
                >拒绝</el-button>
              </template>
              <!-- 所有状态都显示删除按钮 -->
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
              >删除</el-button>
              <!-- 只有管理员才能看到清零按钮 -->
              <el-button
                v-if="isAdmin"
                type="warning"
                size="small"
                @click="handleResetMoney(scope.row)"
              >清零</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container" v-if="driverList.length === 0">
        <el-empty description="暂无符合条件的司机数据"></el-empty>
      </div>
    </el-card>

    <!-- 审核备注对话框 -->
    <el-dialog v-model="approveDialogVisible" title="审核通过" width="400px">
      <el-form label-width="100px">
        <el-form-item label="司机姓名:">
          <span>{{ currentDriver?.name }}</span>
        </el-form-item>
        <el-form-item label="手机号码:">
          <span>{{ currentDriver?.phone }}</span>
        </el-form-item>
        <el-form-item label="审核备注:">
          <el-input v-model="approvalRemark" type="textarea" rows="3" placeholder="请输入审核备注信息（选填）"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="approveDialogVisible = false">取消</el-button>
          <el-button type="success" @click="confirmApprove" :loading="approvalLoading">确认审核</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getAllDrivers, approveDriver, rejectDriver, resetDriverMoney, deleteDriver } from '@/api/driver';
import { useUserStore } from '@/stores/user';
import type { DriverQueryParams, Driver, DriverApprovalRequest, ExtendedUserInfo } from '@/types/interfaces';

const userStore = useUserStore();
const loading = ref(false);
const approvalLoading = ref(false);
const approveDialogVisible = ref(false);
const driverList = ref<Driver[]>([]);
const total = ref(0);
const currentDriver = ref<Driver | null>(null);
const approvalRemark = ref('');

// 添加管理员权限检查
const isAdmin = computed(() => (userStore.getUserInfo() as ExtendedUserInfo)?.role_key === 'admin');

const queryForm = reactive<DriverQueryParams>({
  audit_status: 0, // 默认查询未审核的司机
});

const operatorId = computed(() => userStore.getUserInfo()?.id || 0);

const loadDrivers = async () => {
  loading.value = true;
  try {
    // 获取所有司机，不再使用状态筛选
    const params = {};
    
    const response = await getAllDrivers(params);
    const data = response.data as any;
    if (data.code === 200 && data.data) {
      // 映射后端字段到前端字段
      const rawDrivers = data.data.records || data.data;
      driverList.value = rawDrivers.map((driver: any) => ({
        ...driver,
        auditStatus: driver.audit_status // 将后端的audit_status映射为前端的auditStatus
      }));
      total.value = data.data.total || driverList.value.length;
      
  
    } else {
      driverList.value = [];
      total.value = 0;
      ElMessage.warning(data.message || '获取司机列表失败');
    }
  } catch (error) {
    console.error('获取司机列表失败:', error);
    ElMessage.error('获取司机列表失败，请稍后重试');
    driverList.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

const handleApprove = (row: Driver) => {
  currentDriver.value = row;
  approvalRemark.value = '';
  approveDialogVisible.value = true;
};

const confirmApprove = async () => {
  if (!currentDriver.value || !currentDriver.value.id) {
    ElMessage.error('司机信息不完整');
    return;
  }

  approvalLoading.value = true;
  try {
    const approvalData: DriverApprovalRequest = {
      id: currentDriver.value.id,
      audit_status: 1, // 1=已通过
      remark: approvalRemark.value
    };

    const response = await approveDriver(currentDriver.value.id, approvalData);
    
    if ((response as any).status === 200 || (response as any).status === 201) {
      ElMessage.success('司机审核通过成功');
      approveDialogVisible.value = false;
      await loadDrivers();
    } else {
      throw new Error(response.data?.message || '审核失败');
    }
  } catch (error) {
    console.error('审核失败:', error);
    ElMessage.error('审核失败，请稍后重试');
  } finally {
    approvalLoading.value = false;
  }
};

const handleReject = (row: Driver) => {
  ElMessageBox.confirm(
    `确定要拒绝司机 ${row.name} 的申请吗？`,
    '拒绝确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      try {
        const approvalData: DriverApprovalRequest = {
          id: row.id,
          audit_status: 2, // 2=已拒绝
          remark: '管理员拒绝'
        };

        const response = await rejectDriver(row.id, approvalData);
        if ((response as any).status === 200 || (response as any).status === 204) {
          ElMessage.success('已拒绝该司机申请');
          await loadDrivers();
        } else {
          throw new Error(response.data?.message || '操作失败');
        }
      } catch (error) {
        console.error('拒绝失败:', error);
        ElMessage.error('拒绝失败，请稍后重试');
      }
    })
    .catch(() => {
      // 用户取消操作
    });
};

const handleDelete = (row: Driver) => {
  ElMessageBox.confirm(
    `确定要删除司机 ${row.name} 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      try {
        // 使用删除司机的API调用
        const auditor = userStore.getUserInfo()?.username || 'unknown';
        const response = await deleteDriver(row.id, auditor);
        
        // 检查响应数据中的业务码
        if (response.data && response.data.code === 200) {
          ElMessage.success('已删除该司机');
          await loadDrivers();
        } else {
          // 显示后端返回的具体错误信息
          ElMessage.error(response.data?.message || response.data?.data || '删除失败');
          console.error('删除失败，业务状态码:', response.data?.code, '错误信息:', response.data?.message, '详情:', response.data?.data);
        }
      } catch (error) {
        console.error('删除失败:', error);
        ElMessage.error('删除失败，请稍后重试');
      }
    })
    .catch(() => {
      // 用户取消操作
    });
};

const handleResetMoney = (row: Driver) => {
  // 再次检查权限
  if (!isAdmin.value) {
    ElMessage.error('只有管理员才能进行此操作');
    return;
  }

  ElMessageBox.confirm(
    `确定要清零司机 ${row.name} 的账户余额吗？此操作不可恢复。`,
    '清零确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      try {
        const auditor = userStore.getUserInfo()?.username || 'unknown';
        
        const response = await resetDriverMoney(row.id, auditor);
    
        
        // 检查响应数据中的业务码
        if (response.data && response.data.code === 200) {
          ElMessage.success('已清零该司机账户余额');
          await loadDrivers();
        } else {
          // 显示后端返回的具体错误信息
          ElMessage.error(response.data?.message || response.data?.data || '清零失败');

        }
      } catch (error: any) {


        ElMessage.error(`清零失败，请稍后重试: ${error.message}`);
      }
    })
    .catch(() => {
      // 用户取消操作
  
    });
};

onMounted(() => {
  loadDrivers();
});
</script>

<style scoped>
.driver-approval-container {
  padding: 20px;
}
.driver-list-container {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-title {
  font-size: 16px;
  font-weight: bold;
}
.pagination-container {
  margin-top: 20px;
  text-align: center;
}
.action-buttons {
  display: flex;
  gap: 8px;
}
.button-row {
  display: flex;
  gap: 5px;
}
.button-row-center {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.tag-center {
  display: flex;
  justify-content: center;
}
.no-data {
  padding: 20px;
  text-align: center;
  color: #909399;
}
:deep(.table-header) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: bold;
}
</style> 