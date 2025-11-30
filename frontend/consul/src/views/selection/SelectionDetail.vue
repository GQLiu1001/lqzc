<template>
  <el-dialog
    v-model="dialogVisible"
    title="选品单详情"
    width="80%"
    :before-close="handleClose"
  >
    <div class="detail-container" v-loading="loading">
      <!-- 添加商品区域 -->
      <div class="add-item-section">
        <h3>添加商品</h3>
        <el-form :inline="true" :model="addForm" ref="addFormRef">
          <el-form-item label="商品型号" prop="item_model">
            <el-input v-model="addForm.item_model" placeholder="请输入商品型号" style="width: 180px;" />
          </el-form-item>
          <el-form-item label="销售单价" prop="item_selling_price">
            <el-input-number 
              v-model="addForm.item_selling_price" 
              :precision="2" 
              :min="0" 
              placeholder="单价"
              style="width: 120px;"
            />
          </el-form-item>
          <el-form-item label="数量" prop="amount">
            <el-input-number 
              v-model="addForm.amount" 
              :min="1" 
              placeholder="数量"
              style="width: 100px;"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="addItem" :loading="addLoading">添加商品</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 商品列表 -->
      <div class="items-section">
        <h3>商品明细</h3>
        <el-table :data="itemsList" style="width: 100%">
          <el-table-column prop="item_model" label="商品型号" width="200" />
          <el-table-column prop="item_specification" label="规格" width="150" />
          <el-table-column prop="item_selling_price" label="销售单价" width="120">
            <template #default="scope">
              ¥{{ scope.row.item_selling_price?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="数量" width="100">
            <template #default="scope">
              <el-input-number
                v-if="scope.row.editing"
                v-model="scope.row.tempAmount"
                :min="1"
                :precision="0"
                :step="1"
                size="small"
                style="width: 80px;"
                @change="(value: number | undefined) => scope.row.tempAmount = Number(value || 1)"
              />
              <span v-else>{{ scope.row.amount }}</span>
            </template>
          </el-table-column>
          <el-table-column label="小计" width="120">
            <template #default="scope">
              ¥{{ ((scope.row.item_selling_price || 0) * scope.row.amount).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <template v-if="scope.row.editing">
                <el-button link type="success" @click="saveAmount(scope.row)" :loading="updateLoading">保存</el-button>
                <el-button link @click="cancelEdit(scope.row)">取消</el-button>
              </template>
              <template v-else>
                <el-button link type="primary" @click="editAmount(scope.row)">修改数量</el-button>
                <el-button link type="danger" @click="deleteItem(scope.row)">删除</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>

        <!-- 总计信息 -->
        <div class="total-section">
          <el-row justify="end">
            <el-col :span="8">
              <div class="total-info">
                <p><strong>商品总数：{{ totalItems }}件</strong></p>
                <p><strong>预估总价：¥{{ totalPrice.toFixed(2) }}</strong></p>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  getSelectionListDetail,
  addSelectionItem,
  updateSelectionItemAmount,
  deleteSelectionItem
} from '@/api/selection';
import type { SelectionItemRecord, SelectionItemAddReq } from '@/types/interfaces';

// 扩展商品项接口，添加编辑状态
interface ExtendedSelectionItem extends SelectionItemRecord {
  editing?: boolean;
  tempAmount?: number;
}

// Props
interface Props {
  visible: boolean;
  selectionId: number;
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  selectionId: 0,
});

// Emits
const emit = defineEmits<{
  close: [];
  refresh: [];
}>();

// 响应式数据
const dialogVisible = ref(false);
const loading = ref(false);
const addLoading = ref(false);
const updateLoading = ref(false);
const itemsList = ref<ExtendedSelectionItem[]>([]);

// 添加商品表单
const addFormRef = ref();
const addForm = reactive<SelectionItemAddReq>({
  item_model: '',
  item_selling_price: 0,
  amount: 1,
});

// 计算属性
const totalItems = computed(() => {
  return itemsList.value.reduce((sum, item) => sum + item.amount, 0);
});

const totalPrice = computed(() => {
  return itemsList.value.reduce((sum, item) => sum + (item.item_selling_price || 0) * item.amount, 0);
});

// 监听visible变化
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal;
  if (newVal && props.selectionId) {
    fetchSelectionDetail();
  }
});

watch(dialogVisible, (newVal) => {
  if (!newVal) {
    emit('close');
  }
});

// 获取选品单详情
const fetchSelectionDetail = async () => {
  if (!props.selectionId) return;
  
  loading.value = true;
  try {
    const response = await getSelectionListDetail(props.selectionId);
    const result = response as any;
    if (result.data.code === 200) {
      itemsList.value = result.data.data.map((item: any) => ({
        ...item,
        editing: false,
        tempAmount: Number(item.amount) || 1,
      }));
    } else {
      ElMessage.error(result.data.message || '获取选品单详情失败');
    }
  } catch (error) {
    console.error('获取选品单详情失败:', error);
    ElMessage.error('获取选品单详情失败');
  } finally {
    loading.value = false;
  }
};

// 添加商品
const addItem = async () => {
  if (!addFormRef.value) return;
  
  await addFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      addLoading.value = true;
      try {
        const response = await addSelectionItem(props.selectionId, addForm);
        const result = response as any;
        if (result.data.code === 200) {
          ElMessage.success('添加商品成功');
          // 重置表单
          Object.assign(addForm, {
            item_model: '',
            item_selling_price: 0,
            amount: 1,
          });
          // 刷新列表
          fetchSelectionDetail();
          emit('refresh');
        } else {
          ElMessage.error(result.data.message || '添加商品失败');
        }
      } catch (error) {
        console.error('添加商品失败:', error);
        ElMessage.error('添加商品失败');
      } finally {
        addLoading.value = false;
      }
    }
  });
};

// 编辑数量
const editAmount = (row: ExtendedSelectionItem) => {
  row.editing = true;
  row.tempAmount = Number(row.amount) || 1;
};

// 取消编辑
const cancelEdit = (row: ExtendedSelectionItem) => {
  row.editing = false;
  row.tempAmount = Number(row.amount) || 1;
};

// 保存数量修改
const saveAmount = async (row: ExtendedSelectionItem) => {
  // 确保 tempAmount 是数字类型
  const amount = Number(row.tempAmount);
  
  if (!row.id) {
    ElMessage.error('后端接口返回的数据缺少ID字段，无法修改数量。请联系开发人员修复接口。');
    return;
  }
  
  if (!row.tempAmount && row.tempAmount !== 0) {
    ElMessage.error('请输入数量');
    return;
  }
  
  if (amount < 1 || !Number.isInteger(amount)) {
    ElMessage.error('请输入有效的数量（正整数）');
    return;
  }
  
  updateLoading.value = true;
  try {
    const response = await updateSelectionItemAmount(props.selectionId, row.id, amount);
    const result = response as any;
    if (result.data.code === 200) {
      ElMessage.success('修改数量成功');
      row.amount = amount;
      row.editing = false;
      emit('refresh');
    } else {
      ElMessage.error(result.data.message || '修改数量失败');
    }
  } catch (error) {
    console.error('修改数量失败:', error);
    ElMessage.error('修改数量失败');
  } finally {
    updateLoading.value = false;
  }
};

// 删除商品
const deleteItem = async (row: ExtendedSelectionItem) => {
  if (!row.id) {
    ElMessage.error('后端接口返回的数据缺少ID字段，无法删除商品。请联系开发人员修复接口。');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除商品"${row.item_model}"吗？`, 
      '确认删除', 
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    loading.value = true;
    const response = await deleteSelectionItem(props.selectionId, row.id);
    const result = response as any;
    if (result.data.code === 200) {
      ElMessage.success('删除成功');
      await fetchSelectionDetail();
      emit('refresh');
    } else {
      ElMessage.error(result.data.message || '删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error);
      ElMessage.error('删除失败');
    }
  } finally {
    loading.value = false;
  }
};

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false;
};
</script>

<style scoped>
.detail-container {
  padding: 20px 0;
}

.add-item-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  margin-bottom: 30px;
}

.add-item-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
}

.items-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
}

.total-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
}

.total-info p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}
</style> 