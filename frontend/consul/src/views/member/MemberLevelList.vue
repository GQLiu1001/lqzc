<template>
  <div class="member-level-container">
    <h1>会员等级管理</h1>
    <hr>

    <!-- 操作栏 -->
    <el-card class="search-card">
      <el-button type="primary" @click="handleAdd">新增等级</el-button>
    </el-card>

    <!-- 等级列表 -->
    <el-card class="table-card">
      <el-table :data="levelList" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="level" label="等级编号" width="100" />
        <el-table-column prop="name" label="等级名称" width="120" />
        <el-table-column label="积分区间" width="150">
          <template #default="{ row }">
            {{ row.min_points }} - {{ row.max_points }}
          </template>
        </el-table-column>
        <el-table-column prop="benefits" label="权益描述" min-width="200" />
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchLevelList"
        @current-change="fetchLevelList"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑等级' : '新增等级'"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="等级编号" prop="level">
          <el-input-number v-model="form.level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="等级名称" prop="name">
          <el-input v-model="form.name" placeholder="如：银卡会员" />
        </el-form-item>
        <el-form-item label="最低积分" prop="min_points">
          <el-input-number v-model="form.min_points" :min="0" />
        </el-form-item>
        <el-form-item label="最高积分" prop="max_points">
          <el-input-number v-model="form.max_points" :min="0" />
        </el-form-item>
        <el-form-item label="权益描述" prop="benefits">
          <el-input
            v-model="form.benefits"
            type="textarea"
            :rows="3"
            placeholder="如：包邮/生日券/专属客服"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
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

// 分页
const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
});

// 等级列表
const levelList = ref<any[]>([]);
const loading = ref(false);

// 编辑对话框
const dialogVisible = ref(false);
const isEditing = ref(false);
const formRef = ref<FormInstance>();
const form = reactive({
  id: undefined as number | undefined,
  level: 1,
  name: '',
  min_points: 0,
  max_points: 999,
  benefits: ''
});

const formRules: FormRules = {
  level: [{ required: true, message: '请输入等级编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入等级名称', trigger: 'blur' }],
  min_points: [{ required: true, message: '请输入最低积分', trigger: 'blur' }],
  max_points: [{ required: true, message: '请输入最高积分', trigger: 'blur' }]
};

const submitting = ref(false);

// 查询等级列表
const fetchLevelList = async () => {
  loading.value = true;
  try {
    const params = {
      current: pagination.current,
      size: pagination.size
    };

    const res = await instance.get('/admin/member-level/list', { params });
    if (res.data.code === 200) {
      levelList.value = res.data.data.records || [];
      pagination.total = res.data.data.total || 0;
    } else {
      ElMessage.error(res.data.message || '查询失败');
    }
  } catch (error) {
    console.error('查询等级列表失败:', error);
    ElMessage.error('查询失败');
  } finally {
    loading.value = false;
  }
};

// 新增
const handleAdd = () => {
  isEditing.value = false;
  Object.assign(form, {
    id: undefined,
    level: levelList.value.length + 1,
    name: '',
    min_points: 0,
    max_points: 999,
    benefits: ''
  });
  dialogVisible.value = true;
};

// 编辑
const handleEdit = (row: any) => {
  isEditing.value = true;
  Object.assign(form, {
    id: row.id,
    level: row.level,
    name: row.name,
    min_points: row.min_points,
    max_points: row.max_points,
    benefits: row.benefits
  });
  dialogVisible.value = true;
};

// 对话框关闭
const handleDialogClose = () => {
  formRef.value?.resetFields();
};

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    submitting.value = true;
    try {
      const res = await instance.post('/admin/member-level/save', form);
      if (res.data.code === 200) {
        ElMessage.success(isEditing.value ? '修改成功' : '新增成功');
        dialogVisible.value = false;
        fetchLevelList();
      } else {
        ElMessage.error(res.data.message || '操作失败');
      }
    } catch (error) {
      console.error('保存等级失败:', error);
      ElMessage.error('操作失败');
    } finally {
      submitting.value = false;
    }
  });
};

onMounted(() => {
  fetchLevelList();
});
</script>

<style scoped>
.member-level-container {
  padding: 20px;
}

.search-card,
.table-card {
  margin-bottom: 20px;
}

.el-pagination {
  display: flex;
}
</style>

