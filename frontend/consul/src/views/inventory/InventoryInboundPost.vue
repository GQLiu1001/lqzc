<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { postInboundLog } from '@/api/logs'; // 修正引用的API
import { useUserStore } from '@/stores/user';
import type { LogsInboundReq } from '@/types/interfaces';

// 获取用户信息
const userStore = useUserStore();
const operatorId = userStore.getUserInfo()?.id || undefined;

// 表单数据（与接口请求类型匹配）
const formData = ref<LogsInboundReq>({
  model: '',
  manufacturer: '',
  specification: '',
  surface: 1,
  category: 1,
  warehouse_num: 1,
  selling_price: 0,
  total_amount: 0,
  unit_per_box: 1,
  remark: '',
});

// 表单加载状态
const loading = ref(false);

// 产品分类和表面处理选项（与数据库枚举一致）
const categoryOptions = [
  { label: '墙砖', value: 1 },
  { label: '地砖', value: 2 },
  { label: '胶', value: 3 },
  { label: '洁具', value: 4 }
];
const surfaceOptions = [
  { label: '抛光', value: 1 },
  { label: '哑光', value: 2 },
  { label: '釉面', value: 3 },
  { label: '通体大理石', value: 4 },
  { label: '微晶石', value: 5 },
  { label: '岩板', value: 6 },
];

// 表单验证规则
const rules = reactive({
  model: [
    { required: true, message: '请输入产品型号', trigger: 'blur' },
    { max: 50, message: '产品型号不能超过50个字符', trigger: 'blur' }
  ],
  manufacturer: [
    { required: true, message: '请输入制造厂商', trigger: 'blur' },
    { max: 50, message: '制造厂商不能超过50个字符', trigger: 'blur' }
  ],
  specification: [
    { required: false, message: '请输入规格', trigger: 'blur' },
    { pattern: /^[0-9]+x[0-9]+cm$/, message: '规格格式建议为数字x数字cm，如600x600cm', trigger: 'blur' }
  ],
  surface: [
    { required: false, message: '请选择表面处理', trigger: 'change' }
  ],
  category: [
    { required: true, message: '请选择产品分类', trigger: 'change' }
  ],
  warehouse_num: [
    { required: true, message: '请输入仓库编码', trigger: 'blur' },
    { type: 'number', message: '仓库编码必须为数字', trigger: 'blur' }
  ],
  total_amount: [
    { required: true, message: '请输入总数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '总数量必须大于0', trigger: 'blur' }
  ],
  unit_per_box: [
    { required: true, message: '请输入每箱数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '每箱数量必须大于0', trigger: 'blur' }
  ]
});

// 表单引用
const formRef = ref(null);

// 提交函数（匹配接口 /api/logs/inbound）
const submitInventory = async () => {
  if (!formRef.value) return;

  try {
    // 表单验证
    await (formRef.value as any).validate();

    loading.value = true;

    // 准备提交数据
    const submitData: LogsInboundReq = {
      model: formData.value.model,
      manufacturer: formData.value.manufacturer,
      specification: formData.value.specification,
      surface: Number(formData.value.surface),
      category: Number(formData.value.category),
      warehouse_num: Number(formData.value.warehouse_num),
      selling_price: Number(formData.value.selling_price),
      total_amount: Number(formData.value.total_amount),
      unit_per_box: Number(formData.value.unit_per_box),
      remark: formData.value.remark || '',
    };

    // API调用
    const response = await postInboundLog(submitData);

    if (response.data.code === 200 || response.data.code === 201) {
      ElMessage.success('入库记录提交成功');
      resetForm();
    } else {
      ElMessage.error(response.data.message || '提交失败，请检查数据后重试');
    }
  } catch (error) {
    console.error('提交失败:', error);
    ElMessage.error('提交失败，请检查表单数据或稍后重试');
  } finally {
    loading.value = false;
  }
};

// 重置表单函数
const resetForm = () => {
  if (formRef.value) {
    (formRef.value as any).resetFields();
  }

  formData.value = {
    model: '',
    manufacturer: '',
    specification: '',
    surface: 1,
    category: 1,
    warehouse_num: 1,
    selling_price: 0,
    total_amount: 0,
    unit_per_box: 1,
    remark: '',
  };
};

// 计算总箱数
const totalBoxes = computed(() => {
  if (!formData.value.total_amount || !formData.value.unit_per_box || formData.value.unit_per_box <= 0) {
    return '未知';
  }
  return Math.ceil(formData.value.total_amount / formData.value.unit_per_box);
});

// 计算属性：是否显示规格和表面处理字段
const showSpecificationAndSurface = computed(() => {
  return [1, 2].includes(formData.value.category || 0);
});

// 计算属性：是否显示每箱数量字段
const showUnitPerBox = computed(() => {
  return [1, 2].includes(formData.value.category || 0);
});

// 计算属性：总数量的标签文本
const totalLabel = computed(() => {
  return [1, 2].includes(formData.value.category || 0) ? '总片数' : '总个数';
});
</script>

<template>
  <div class="inbound-form-container">
    <h1>提交入库</h1>
    <el-divider />

    <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
        class="inbound-form"
        status-icon
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="产品型号" prop="model">
            <el-input v-model="formData.model" placeholder="请输入产品型号" maxlength="50" show-word-limit />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="制造厂商" prop="manufacturer">
            <el-input v-model="formData.manufacturer" placeholder="请输入制造厂商" maxlength="50" show-word-limit />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="产品分类" prop="category">
            <el-radio-group v-model="formData.category">
              <el-radio
                  v-for="item in categoryOptions"
                  :key="item.value"
                  :label="item.value"
                  class="radio-item"
              >
                {{ item.label }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20" v-if="showSpecificationAndSurface">
        <el-col :span="12">
          <el-form-item label="规格" prop="specification">
            <el-input v-model="formData.specification" placeholder="请输入规格（如600x600cm）" />
            <div class="form-tip">格式：宽x高cm，例如：600x600cm</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="表面处理" prop="surface">
            <el-radio-group v-model="formData.surface">
              <el-radio
                  v-for="item in surfaceOptions"
                  :key="item.value"
                  :label="item.value"
                  class="radio-item"
              >
                {{ item.label }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="仓库编码" prop="warehouse_num">
            <el-input v-model.number="formData.warehouse_num" placeholder="请输入仓库编码" type="number" min="1" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="showUnitPerBox ? 8 : 12">
          <el-form-item :label="totalLabel" prop="total_amount">
            <el-input 
                v-model.number="formData.total_amount" 
                :placeholder="'请输入' + totalLabel" 
                type="number" 
                min="1"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8" v-if="showUnitPerBox">
          <el-form-item label="每箱数量" prop="unit_per_box">
            <el-input v-model.number="formData.unit_per_box" placeholder="请输入每箱数量" type="number" min="1" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="16">
          <el-form-item label="备注" prop="remark">
            <el-input
                v-model="formData.remark"
                placeholder="请输入备注（可选）"
                type="textarea"
                rows="3"
                maxlength="500"
                show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <div class="summary-info">
            <div class="summary-title">入库信息摘要</div>
            <div class="summary-item">
              <span class="label">{{ totalLabel }}:</span>
              <span class="value">{{ formData.total_amount || '未设置' }}</span>
            </div>
            <div class="summary-item" v-if="showUnitPerBox">
              <span class="label">每箱数量:</span>
              <span class="value">{{ formData.unit_per_box || '未设置' }}</span>
            </div>
            <div class="summary-item" v-if="showUnitPerBox">
              <span class="label">总箱数:</span>
              <span class="value">{{ totalBoxes }}</span>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-form-item>
        <el-button type="primary" :loading="loading" @click="submitInventory">提交入库</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.inbound-form-container {
  padding: 0 20px 40px;
}

h1 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 20px;
}

.inbound-form {
  margin-top: 30px;
}

.radio-item {
  margin-right: 16px;
  margin-bottom: 8px;
  display: inline-block;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 4px;
}

.summary-info {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  height: 100%;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.summary-title {
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
  font-size: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.summary-item .label {
  color: #606266;
}

.summary-item .value {
  color: #303133;
  font-weight: 500;
}
</style>