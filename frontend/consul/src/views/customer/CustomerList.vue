<template>
  <div class="customer-container">
    <h1>客户管理</h1>
    <hr>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="手机号或昵称"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="会员等级">
          <el-select
            v-model="searchForm.level"
            placeholder="全部"
            clearable
            class="filter-select"
          >
            <el-option label="全部" :value="undefined" />
            <el-option label="普通会员" :value="1" />
            <el-option label="银卡会员" :value="2" />
            <el-option label="金卡会员" :value="3" />
            <el-option label="钻石会员" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            class="filter-select"
          >
            <el-option label="全部" :value="undefined" />
            <el-option label="正常" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">创建客户</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 客户列表 -->
    <el-card class="table-card">
      <el-table :data="customerList" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="头像" width="80">
          <template #default="{ row }">
            <el-avatar :src="row.avatar || '/default-avatar.png'" :size="40" />
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="会员等级" width="120">
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.level)">
              {{ getLevelName(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="register_channel" label="注册渠道" width="100" />
        <el-table-column prop="create_time" label="注册时间" width="180" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row.id)">
              详情
            </el-button>
            <el-button
              :type="row.status === 1 ? 'danger' : 'success'"
              size="small"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="handleSearch"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 创建客户对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建客户"
      width="500px"
      @close="handleCreateDialogClose"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" placeholder="请输入手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="createForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="不填则默认手机号后6位"
          />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="createForm.gender">
            <el-radio :label="0">保密</el-radio>
            <el-radio :label="1">男</el-radio>
            <el-radio :label="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="createForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 状态变更对话框 -->
    <el-dialog
      v-model="statusDialogVisible"
      :title="currentCustomer?.status === 1 ? '停用客户' : '启用客户'"
      width="400px"
    >
      <el-form :model="statusForm" label-width="80px">
        <el-form-item label="原因" v-if="currentCustomer?.status === 1">
          <el-input
            v-model="statusForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入停用原因"
          />
        </el-form-item>
        <el-alert
          v-else
          title="确认要启用该客户吗?"
          type="warning"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleStatusSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { useRouter } from 'vue-router';
import {
  getAdminCustomerList,
  createCustomer,
  updateCustomerStatus,
  type CustomerListParams,
  type CreateCustomerRequest,
  type UpdateCustomerStatusRequest
} from '@/api/customer';

const router = useRouter();

// 搜索表单
const searchForm = reactive<CustomerListParams>({
  keyword: '',
  level: undefined,
  status: undefined
});

// 分页
const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
});

// 客户列表
const customerList = ref<any[]>([]);
const loading = ref(false);

// 创建客户对话框
const createDialogVisible = ref(false);
const createFormRef = ref<FormInstance>();
const createForm = reactive<CreateCustomerRequest>({
  phone: '',
  nickname: '',
  password: '',
  gender: 0,
  remark: ''
});

const createRules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' }
  ]
};

// 状态变更对话框
const statusDialogVisible = ref(false);
const currentCustomer = ref<any>(null);
const statusForm = reactive<UpdateCustomerStatusRequest>({
  status: 0,
  reason: ''
});

const submitting = ref(false);

// 会员等级名称映射
const getLevelName = (level: number): string => {
  const levelMap: Record<number, string> = {
    1: '普通会员',
    2: '银卡会员',
    3: '金卡会员',
    4: '钻石会员'
  };
  return levelMap[level] || '未知';
};

// 会员等级标签类型映射
const getLevelTagType = (level: number): string => {
  const typeMap: Record<number, string> = {
    1: 'info',
    2: '',
    3: 'warning',
    4: 'danger'
  };
  return typeMap[level] || 'info';
};

// 查询客户列表
const fetchCustomerList = async () => {
  loading.value = true;
  try {
    const params = {
      current: pagination.current,
      size: pagination.size,
      ...searchForm
    };
    const res = await getAdminCustomerList(params);
    if (res.data.code === 200) {
      customerList.value = res.data.data.records || [];
      pagination.total = res.data.data.total || 0;
    } else {
      ElMessage.error(res.data.message || '查询失败');
    }
  } catch (error) {
    console.error('查询客户列表失败:', error);
    ElMessage.error('查询失败');
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  pagination.current = 1;
  fetchCustomerList();
};

// 重置
const handleReset = () => {
  searchForm.keyword = '';
  searchForm.level = undefined;
  searchForm.status = undefined;
  handleSearch();
};

// 创建客户
const handleCreate = () => {
  createDialogVisible.value = true;
};

// 创建对话框关闭
const handleCreateDialogClose = () => {
  createFormRef.value?.resetFields();
  Object.assign(createForm, {
    phone: '',
    nickname: '',
    password: '',
    gender: 0,
    remark: ''
  });
};

// 提交创建
const handleCreateSubmit = async () => {
  if (!createFormRef.value) return;
  
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return;
    
    submitting.value = true;
    try {
      const res = await createCustomer(createForm);
      if (res.data.code === 200) {
        ElMessage.success('创建成功');
        createDialogVisible.value = false;
        fetchCustomerList();
      } else {
        ElMessage.error(res.data.message || '创建失败');
      }
    } catch (error) {
      console.error('创建客户失败:', error);
      ElMessage.error('创建失败');
    } finally {
      submitting.value = false;
    }
  });
};

// 查看详情
const handleViewDetail = (id: number) => {
  router.push(`/dashboard/customer/detail/${id}`);
};

// 切换状态
const handleToggleStatus = (row: any) => {
  currentCustomer.value = row;
  statusForm.status = row.status === 1 ? 0 : 1;
  statusForm.reason = '';
  statusDialogVisible.value = true;
};

// 提交状态变更
const handleStatusSubmit = async () => {
  if (!currentCustomer.value) return;
  
  submitting.value = true;
  try {
    const res = await updateCustomerStatus(currentCustomer.value.id, statusForm);
    if (res.data.code === 200) {
      ElMessage.success('操作成功');
      statusDialogVisible.value = false;
      fetchCustomerList();
    } else {
      ElMessage.error(res.data.message || '操作失败');
    }
  } catch (error) {
    console.error('更新客户状态失败:', error);
    ElMessage.error('操作失败');
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchCustomerList();
});
</script>

<style scoped>
.customer-container {
  padding: 20px;
}

.search-card,
.table-card {
  margin-bottom: 20px;
}

.filter-select {
  width: 150px;
}

.el-pagination {
  display: flex;
}
</style>
