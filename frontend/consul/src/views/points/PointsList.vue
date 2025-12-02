<template>
  <div class="points-container">
    <h1>积分管理</h1>
    <hr>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="客户手机号">
          <el-input
            v-model="searchForm.customerPhone"
            placeholder="手机号"
            clearable
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item label="来源类型">
          <el-select
            v-model="searchForm.sourceType"
            placeholder="全部"
            clearable
            style="width: 130px"
          >
            <el-option label="全部" :value="undefined" />
            <el-option label="下单赠送" :value="1" />
            <el-option label="退款回退" :value="2" />
            <el-option label="支付抵扣" :value="3" />
            <el-option label="人工调整" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="warning" @click="handleAdjust">人工调整</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 流水列表 -->
    <el-card class="table-card">
      <el-table :data="logList" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="customer_phone" label="客户手机号" width="130" />
        <el-table-column label="变动积分" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.change_amount > 0 ? '#67c23a' : '#f56c6c' }">
              {{ row.change_amount > 0 ? '+' : '' }}{{ row.change_amount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="变动后余额" width="120" />
        <el-table-column label="来源类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getSourceTagType(row.source_type)">
              {{ getSourceName(row.source_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order_id" label="关联订单" width="100" />
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column prop="create_time" label="创建时间" width="180" />
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchLogList"
        @current-change="fetchLogList"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 人工调整对话框 -->
    <el-dialog
      v-model="adjustDialogVisible"
      title="人工调整积分"
      width="500px"
    >
      <el-form
        ref="adjustFormRef"
        :model="adjustForm"
        :rules="adjustRules"
        label-width="100px"
      >
        <el-form-item label="选择客户" prop="customer_id">
          <el-select
            v-model="adjustForm.customer_id"
            filterable
            remote
            reserve-keyword
            placeholder="输入手机号或昵称搜索"
            :remote-method="searchCustomers"
            :loading="customerLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in customerOptions"
              :key="item.id"
              :label="`${item.nickname} (${item.phone})`"
              :value="item.id"
            >
              <span style="float: left">{{ item.nickname }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">{{ item.phone }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="变动积分" prop="change_amount">
          <el-input-number v-model="adjustForm.change_amount" style="width: 100%" />
          <div class="form-tip">正数增加，负数扣除</div>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="adjustForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入调整原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adjustDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdjustSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import instance from '@/utils/axios';

// 搜索表单
const searchForm = reactive({
  customerPhone: '',
  sourceType: undefined as number | undefined,
  dateRange: [] as string[]
});

// 分页
const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
});

// 流水列表
const logList = ref<any[]>([]);
const loading = ref(false);

// 人工调整对话框
const adjustDialogVisible = ref(false);
const adjustFormRef = ref<FormInstance>();
const adjustForm = reactive({
  customer_id: undefined as number | undefined,
  change_amount: 0,
  remark: ''
});

const adjustRules: FormRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  change_amount: [{ required: true, message: '请输入变动积分', trigger: 'blur' }]
};

const submitting = ref(false);

// 客户选择器
const customerLoading = ref(false);
const customerOptions = ref<any[]>([]);

// 来源类型映射
const getSourceName = (type: number): string => {
  const map: Record<number, string> = { 1: '下单赠送', 2: '退款回退', 3: '支付抵扣', 4: '人工调整' };
  return map[type] || '未知';
};

const getSourceTagType = (type: number): string => {
  const map: Record<number, string> = { 1: 'success', 2: 'warning', 3: 'danger', 4: 'info' };
  return map[type] || 'info';
};

// 查询流水列表
const fetchLogList = async () => {
  loading.value = true;
  try {
    const params: any = {
      current: pagination.current,
      size: pagination.size
    };
    if (searchForm.customerPhone) params.customerPhone = searchForm.customerPhone;
    if (searchForm.sourceType !== undefined) params.sourceType = searchForm.sourceType;
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.dateRange = searchForm.dateRange.join(',');
    }

    const res = await instance.get('/admin/points/log/list', { params });
    if (res.data.code === 200) {
      logList.value = res.data.data.records || [];
      pagination.total = res.data.data.total || 0;
    } else {
      ElMessage.error(res.data.message || '查询失败');
    }
  } catch (error) {
    console.error('查询积分流水失败:', error);
    ElMessage.error('查询失败');
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  pagination.current = 1;
  fetchLogList();
};

// 重置
const handleReset = () => {
  searchForm.customerPhone = '';
  searchForm.sourceType = undefined;
  searchForm.dateRange = [];
  handleSearch();
};

// 搜索客户
const searchCustomers = async (keyword: string) => {
  if (!keyword) {
    customerOptions.value = [];
    return;
  }
  customerLoading.value = true;
  try {
    const res = await instance.get('/customer/list', {
      params: { keyword, size: 20 }
    });
    if (res.data.code === 200) {
      customerOptions.value = res.data.data || [];
    }
  } catch (error) {
    console.error('搜索客户失败:', error);
  } finally {
    customerLoading.value = false;
  }
};

// 打开人工调整对话框
const handleAdjust = () => {
  adjustForm.customer_id = undefined;
  adjustForm.change_amount = 0;
  adjustForm.remark = '';
  customerOptions.value = [];
  adjustDialogVisible.value = true;
};

// 提交人工调整
const handleAdjustSubmit = async () => {
  if (!adjustFormRef.value) return;

  await adjustFormRef.value.validate(async (valid) => {
    if (!valid) return;

    submitting.value = true;
    try {
      const res = await instance.post('/admin/points/adjust', adjustForm);
      if (res.data.code === 200) {
        ElMessage.success('调整成功');
        adjustDialogVisible.value = false;
        fetchLogList();
      } else {
        ElMessage.error(res.data.message || '调整失败');
      }
    } catch (error) {
      console.error('调整积分失败:', error);
      ElMessage.error('调整失败');
    } finally {
      submitting.value = false;
    }
  });
};

onMounted(() => {
  fetchLogList();
});
</script>

<style scoped>
.points-container {
  padding: 20px;
}

.search-card,
.table-card {
  margin-bottom: 20px;
}

.el-pagination {
  display: flex;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

