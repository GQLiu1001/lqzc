<template>
  <div class="coupon-container">
    <h1>优惠券管理</h1>
    <hr>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="标题">
          <el-input
            v-model="searchForm.title"
            placeholder="优惠券标题"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            class="filter-select"
          >
            <el-option label="全部" :value="undefined" />
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">创建优惠券</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 优惠券列表 -->
    <el-card class="table-card">
      <el-table :data="couponList" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ getTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_issued" label="发行量" width="100" />
        <el-table-column prop="received_count" label="已领取" width="100" />
        <el-table-column prop="used_count" label="已核销" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            <div>{{ formatDate(row.valid_from) }}</div>
            <div>至 {{ formatDate(row.valid_to) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewRecords(row.id)">
              发放记录
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

    <!-- 创建优惠券对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建优惠券"
      width="600px"
      top="8vh"
      class="create-dialog"
      @close="handleCreateDialogClose"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入优惠券标题" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="createForm.type">
            <el-radio :label="1">满减券</el-radio>
            <el-radio :label="2">折扣券</el-radio>
            <el-radio :label="3">现金券</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="使用门槛" prop="threshold_amount" v-if="createForm.type === 1">
          <el-input-number v-model="createForm.threshold_amount" :min="0" :precision="2" />
          <span style="margin-left: 8px">元</span>
        </el-form-item>
        <el-form-item label="立减金额" prop="discount_amount" v-if="createForm.type === 1 || createForm.type === 3">
          <el-input-number v-model="createForm.discount_amount" :min="0" :precision="2" />
          <span style="margin-left: 8px">元</span>
        </el-form-item>
        <el-form-item label="折扣率" prop="discount_rate" v-if="createForm.type === 2">
          <el-input-number v-model="createForm.discount_rate" :min="0.1" :max="0.99" :precision="2" :step="0.05" />
          <span style="margin-left: 8px">（0.9表示9折）</span>
        </el-form-item>
        <el-form-item label="折扣封顶" prop="max_discount" v-if="createForm.type === 2">
          <el-input-number v-model="createForm.max_discount" :min="0" :precision="2" />
          <span style="margin-left: 8px">元（可不填）</span>
        </el-form-item>
        <el-form-item label="发行总量" prop="total_issued">
          <el-input-number v-model="createForm.total_issued" :min="1" />
        </el-form-item>
        <el-form-item label="每人限领" prop="per_user_limit">
          <el-input-number v-model="createForm.per_user_limit" :min="1" />
        </el-form-item>
        <el-form-item label="有效期" prop="valid_range">
          <el-date-picker
            v-model="createForm.valid_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            :teleported="true"
            popper-class="date-picker-popper"
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

    <!-- 发放记录对话框 -->
    <el-dialog
      v-model="recordDialogVisible"
      title="发放记录"
      width="800px"
    >
      <el-form :inline="true" :model="recordSearchForm" style="margin-bottom: 16px">
        <el-form-item label="手机号">
          <el-input v-model="recordSearchForm.customerPhone" placeholder="客户手机号" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="recordSearchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" :value="undefined" />
            <el-option label="未使用" :value="0" />
            <el-option label="已使用" :value="1" />
            <el-option label="已过期" :value="2" />
            <el-option label="已作废" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchRecords">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="recordList" v-loading="recordLoading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="customer_phone" label="客户手机号" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="use_time" label="使用时间" min-width="180" />
      </el-table>
      <el-pagination
        v-model:current-page="recordPagination.current"
        v-model:page-size="recordPagination.size"
        :total="recordPagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchRecords"
        @current-change="fetchRecords"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import instance from '@/utils/axios';

// 搜索表单
const searchForm = reactive({
  title: '',
  status: undefined as number | undefined
});

// 分页
const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
});

// 优惠券列表
const couponList = ref<any[]>([]);
const loading = ref(false);

// 创建优惠券对话框
const createDialogVisible = ref(false);
const createFormRef = ref<FormInstance>();
const createForm = reactive({
  title: '',
  type: 1,
  threshold_amount: 0,
  discount_amount: 0,
  discount_rate: 0.9,
  max_discount: undefined as number | undefined,
  total_issued: 100,
  per_user_limit: 1,
  valid_range: [] as string[]
});

const createRules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  total_issued: [{ required: true, message: '请输入发行总量', trigger: 'blur' }],
  valid_range: [{ required: true, message: '请选择有效期', trigger: 'change' }]
};

// 发放记录对话框
const recordDialogVisible = ref(false);
const currentTemplateId = ref<number | null>(null);
const recordSearchForm = reactive({
  customerPhone: '',
  status: undefined as number | undefined
});
const recordList = ref<any[]>([]);
const recordLoading = ref(false);
const recordPagination = reactive({
  current: 1,
  size: 10,
  total: 0
});

const submitting = ref(false);

// 类型名称映射
const getTypeName = (type: number): string => {
  const map: Record<number, string> = { 1: '满减', 2: '折扣', 3: '现金' };
  return map[type] || '未知';
};

const getTypeTagType = (type: number): string => {
  const map: Record<number, string> = { 1: 'warning', 2: 'success', 3: 'danger' };
  return map[type] || 'info';
};

// 状态名称映射
const getStatusName = (status: number): string => {
  const map: Record<number, string> = { 0: '未使用', 1: '已使用', 2: '已过期', 3: '已作废' };
  return map[status] || '未知';
};

const getStatusTagType = (status: number): string => {
  const map: Record<number, string> = { 0: 'info', 1: 'success', 2: 'warning', 3: 'danger' };
  return map[status] || 'info';
};

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '';
  return new Date(date).toLocaleString('zh-CN');
};

// 查询优惠券列表
const fetchCouponList = async () => {
  loading.value = true;
  try {
    const params: any = {
      current: pagination.current,
      size: pagination.size
    };
    if (searchForm.title) params.title = searchForm.title;
    if (searchForm.status !== undefined) params.status = searchForm.status;

    const res = await instance.get('/admin/coupon/list', { params });
    if (res.data.code === 200) {
      couponList.value = res.data.data.records || [];
      pagination.total = res.data.data.total || 0;
    } else {
      ElMessage.error(res.data.message || '查询失败');
    }
  } catch (error) {
    console.error('查询优惠券列表失败:', error);
    ElMessage.error('查询失败');
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  pagination.current = 1;
  fetchCouponList();
};

// 重置
const handleReset = () => {
  searchForm.title = '';
  searchForm.status = undefined;
  handleSearch();
};

// 创建优惠券
const handleCreate = () => {
  createDialogVisible.value = true;
};

// 创建对话框关闭
const handleCreateDialogClose = () => {
  createFormRef.value?.resetFields();
  Object.assign(createForm, {
    title: '',
    type: 1,
    threshold_amount: 0,
    discount_amount: 0,
    discount_rate: 0.9,
    max_discount: undefined,
    total_issued: 100,
    per_user_limit: 1,
    valid_range: []
  });
};

// 提交创建
const handleCreateSubmit = async () => {
  if (!createFormRef.value) return;

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return;

    // 额外校验有效期
    if (!createForm.valid_range || createForm.valid_range.length < 2) {
      ElMessage.error('请选择有效期');
      return;
    }

    submitting.value = true;
    try {
      const data: any = {
        title: createForm.title,
        type: createForm.type,
        total_issued: createForm.total_issued,
        per_user_limit: createForm.per_user_limit,
        valid_from: createForm.valid_range[0],
        valid_to: createForm.valid_range[1]
      };

      // 根据类型设置对应字段
      if (createForm.type === 1) {
        data.threshold_amount = createForm.threshold_amount;
        data.discount_amount = createForm.discount_amount;
      } else if (createForm.type === 2) {
        data.discount_rate = createForm.discount_rate;
        data.max_discount = createForm.max_discount;
      } else if (createForm.type === 3) {
        data.discount_amount = createForm.discount_amount;
      }

      console.log('创建优惠券请求数据:', data);
      const res = await instance.post('/admin/coupon/create', data);
      if (res.data.code === 200) {
        ElMessage.success('创建成功');
        createDialogVisible.value = false;
        fetchCouponList();
      } else {
        ElMessage.error(res.data.message || '创建失败');
      }
    } catch (error) {
      console.error('创建优惠券失败:', error);
      ElMessage.error('创建失败');
    } finally {
      submitting.value = false;
    }
  });
};

// 查看发放记录
const handleViewRecords = (templateId: number) => {
  currentTemplateId.value = templateId;
  recordSearchForm.customerPhone = '';
  recordSearchForm.status = undefined;
  recordPagination.current = 1;
  recordDialogVisible.value = true;
  fetchRecords();
};

// 查询发放记录
const fetchRecords = async () => {
  if (!currentTemplateId.value) return;

  recordLoading.value = true;
  try {
    const params: any = {
      current: recordPagination.current,
      size: recordPagination.size,
      templateId: currentTemplateId.value
    };
    if (recordSearchForm.customerPhone) params.customerPhone = recordSearchForm.customerPhone;
    if (recordSearchForm.status !== undefined) params.status = recordSearchForm.status;

    const res = await instance.get('/admin/coupon/record/list', { params });
    if (res.data.code === 200) {
      recordList.value = res.data.data.records || [];
      recordPagination.total = res.data.data.total || 0;
    } else {
      ElMessage.error(res.data.message || '查询失败');
    }
  } catch (error) {
    console.error('查询发放记录失败:', error);
    ElMessage.error('查询失败');
  } finally {
    recordLoading.value = false;
  }
};

// 切换状态
const handleToggleStatus = (row: any) => {
  const action = row.status === 1 ? '停用' : '启用';
  ElMessageBox.confirm(`确定要${action}该优惠券吗?`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const newStatus = row.status === 1 ? 0 : 1;
      const res = await instance.put(`/admin/coupon/status/${row.id}`, null, {
        params: { status: newStatus }
      });
      if (res.data.code === 200) {
        ElMessage.success(`${action}成功`);
        fetchCouponList();
      } else {
        ElMessage.error(res.data.message || `${action}失败`);
      }
    } catch (error) {
      console.error('更新状态失败:', error);
      ElMessage.error(`${action}失败`);
    }
  }).catch(() => {});
};

onMounted(() => {
  fetchCouponList();
});
</script>

<style scoped>
.coupon-container {
  padding: 20px;
}

.search-card,
.table-card {
  margin-bottom: 20px;
}

.filter-select {
  width: 120px;
}

.el-pagination {
  display: flex;
}
</style>

<style>
/* 日期选择器弹窗全局样式 */
.date-picker-popper {
  z-index: 9999 !important;
}
</style>
