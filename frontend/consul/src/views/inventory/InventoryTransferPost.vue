<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { createTransferLog } from '@/api/inventoryLog';
import { useUserStore } from '@/stores/user';
import type { LogsTransferReq } from '@/types/interfaces';

// 获取用户信息
const userStore = useUserStore();
const operatorId = userStore.getUserInfo()?.id;

// Form data
const formData = ref<LogsTransferReq>({
  item_id: 0,
  log_type: 3, // 固定为调拨
  source_warehouse: 0,
  target_warehouse: 0,
  remark: '',
});

// Submit function
const submitTransfer = async () => {
  try {
    // Validate required fields
    const requiredFields = {
      item_id: '库存项ID',
      source_warehouse: '源仓库',
      target_warehouse: '目标仓库',
    };

    for (const [field, label] of Object.entries(requiredFields)) {
      const value = formData.value[field as keyof LogsTransferReq];
      if (value === undefined || value === null || value === '') {
        ElMessage.error(`请填写${label}`);
        return;
      }
    }

    // Validate warehouses are different
    if (formData.value.source_warehouse === formData.value.target_warehouse) {
      ElMessage.error('源仓库和目标仓库不能相同');
      return;
    }

    // Validate warehouse numbers (1-5)
    if (formData.value.source_warehouse! < 1 || formData.value.source_warehouse! > 5) {
      ElMessage.error('源仓库编号必须在1-5之间');
      return;
    }
    if (formData.value.target_warehouse! < 1 || formData.value.target_warehouse! > 5) {
      ElMessage.error('目标仓库编号必须在1-5之间');
      return;
    }

    // API call
    const response = await createTransferLog(formData.value);
    if (response.data.code === 200) {
      ElMessage.success('调拨记录创建成功');
      resetForm();
    } else {
      throw new Error(response.data.message || '响应状态异常');
    }
  } catch (error) {
    console.error('Submission failed:', error);
    ElMessage.error('调拨记录创建失败，请稍后重试');
  }
};

// Reset form function
const resetForm = () => {
  formData.value = {
    item_id: 0,
    log_type: 3, // 固定为调拨
    source_warehouse: 0,
    target_warehouse: 0,
    remark: '',
  };
};
</script>

<template>
  <h1>创建调拨记录</h1>
  <hr>
  <div class="form-container">
    <el-form :model="formData" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="库存项ID" required>
            <el-input-number
                v-model="formData.item_id"
                placeholder="请输入库存项ID"
                :min="1"
                controls-position="right"
                style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="源仓库" required>
            <el-input-number
                v-model="formData.source_warehouse"
                placeholder="请输入源仓库编号（1-5）"
                :min="1"
                :max="5"
                controls-position="right"
                style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标仓库" required>
            <el-input-number
                v-model="formData.target_warehouse"
                placeholder="请输入目标仓库编号（1-5）"
                :min="1"
                :max="5"
                controls-position="right"
                style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input
                v-model="formData.remark"
                type="textarea"
                placeholder="请输入备注信息，如：从1号仓调到2号仓"
                :rows="3"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item>
        <el-button type="primary" @click="submitTransfer">提交调拨</el-button>
        <el-button @click="resetForm">重置表单</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-container {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}

:deep(.el-input-number) {
  width: 100%;
}

.el-form-item {
  margin-bottom: 24px;
}

.el-button {
  margin-right: 12px;
}
</style>