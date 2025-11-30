<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, ZoomIn } from '@element-plus/icons-vue';
import { getInventoryItems, updateInventoryItem, deleteInventoryItem } from '@/api/inventory';
import { uploadImage } from '@/api/upload';
import type { InventoryItem, InventoryQueryParams } from '@/types/interfaces.ts';
import type { UploadImageResp } from '@/api/upload';
import { useUserStore } from '@/stores/user';

// 用户权限检查
const userStore = useUserStore();
const isAdmin = userStore.isAdmin();

// 搜索参数
const category = ref<number | null>(null); // 产品分类
const surface = ref<number | null>(null); // 表面处理
const searchResults = ref<InventoryItem[]>([]); // 存储搜索结果
const total = ref(0); // 总记录数
const page = ref(1); // 当前页码
const size = ref(10); // 每页记录数
const loading = ref(false); // 加载状态

// 编辑对话框控制
const editDialogVisible = ref(false);
const editForm = ref<InventoryItem>({
  id: 0,
  model: '',
  manufacturer: '',
  specification: '',
  surface: 0,
  category: 0,
  warehouse_num: 0,
  total_amount: 0,
  unit_per_box: 0,
  selling_price: 0,
  picture: '',
  remark: '',
  create_time: '',
  update_time: '',
});

// 图片相关变量
const imagePreviewVisible = ref(false);
const previewImageUrl = ref('');
const uploadLoading = ref(false);

// 分类和表面处理选项（与数据库枚举一致）
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

// 表单校验规则
const formRules = reactive({
  model: [
    { required: true, message: '请输入产品型号', trigger: 'blur' },
    { max: 50, message: '产品型号不能超过50个字符', trigger: 'blur' }
  ],
  manufacturer: [
    { required: true, message: '请输入制造厂商', trigger: 'blur' },
    { max: 50, message: '制造厂商不能超过50个字符', trigger: 'blur' }
  ],
  specification: [
    { required: true, message: '请输入规格', trigger: 'blur' }
  ],
  surface: [{ required: true, message: '请选择表面处理', trigger: 'change' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  warehouse_num: [
    { required: true, message: '请输入仓库编码', trigger: 'blur' },
    { type: 'number', message: '仓库编码必须为数字', trigger: 'blur' }
  ],
  total_amount: [
    { required: true, message: '请输入总数量', trigger: 'blur' },
    { type: 'number', min: 0, message: '总数量不能小于0', trigger: 'blur' }
  ],
  unit_per_box: [
    { required: true, message: '请输入每箱数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '每箱数量至少为1', trigger: 'blur' }
  ]
});

// 计算属性：根据分类显示不同的单位
const getUnitLabel = (category: number) => {
  return [1, 2].includes(category) ? '片' : '个';
};

// 计算总箱数
const calculateTotalBoxes = (row: InventoryItem) => {
  if (!row.total_amount || !row.unit_per_box || row.unit_per_box <= 0) {
    return '-';
  }

  const boxes = Math.floor(row.total_amount / row.unit_per_box);
  const remainingPieces = row.total_amount % row.unit_per_box;

  if (boxes > 0 && remainingPieces > 0) {
    return `${boxes}箱${remainingPieces}${getUnitLabel(row.category)}`;
  } else if (boxes > 0) {
    return `${boxes}箱`;
  } else {
    return `${remainingPieces}${getUnitLabel(row.category)}`;
  }
};

// 计算属性：总数量的标签文本
const totalLabel = computed(() => {
  return [1, 2].includes(editForm.value.category) ? '总片数' : '总个数';
});

// 计算属性：每箱数量的标签文本
const boxLabel = computed(() => {
  return [1, 2].includes(editForm.value.category) ? '每箱片数' : '每箱个数';
});

// 计算属性：表格列标题
const columnLabels = computed(() => ({
  total: `总${getUnitLabel(category.value || 0)}数`,
  box: `每箱${getUnitLabel(category.value || 0)}数`
}));

// 添加排序方法
const sortInventoryItems = (list: InventoryItem[]) => {
  return [...list].sort((a, b) => {
    const idA = a.id || 0;
    const idB = b.id || 0;
    return idB - idA; // 降序排序
  });
};

// 搜索函数（匹配接口 /api/inventory/items）
const performSearch = async () => {
  loading.value = true;
  try {
    const params: InventoryQueryParams = {
      current: page.value,
      size: size.value
    };
    if (category.value !== null) params.category = category.value.toString();
    if (surface.value !== null) params.surface = surface.value.toString();

    const response: any = await getInventoryItems(params);
    if (response.data.code === 200 && response.data.data?.records) {
      // 对数据进行排序
      searchResults.value = sortInventoryItems(response.data.data.records);
      total.value = response.data.data.total || 0;
    } else {
      searchResults.value = [];
      total.value = 0;
      ElMessage.warning('未找到匹配的数据');
    }
  } catch (error) {
    console.error('搜索失败:', error);
    searchResults.value = [];
    total.value = 0;
    ElMessage.error('获取数据失败，请检查网络连接或联系管理员');
  } finally {
    loading.value = false;
  }
};

// 编辑记录（匹配接口 /api/inventory/items/{id}）
const handleEdit = (row: InventoryItem) => {
  editForm.value = { ...row };
  editDialogVisible.value = true;
};

const formRef = ref(null);

const saveEdit = async () => {
  if (!formRef.value) return;

  try {
    await (formRef.value as any).validate();

    const updateData: any = {
      id: editForm.value.id,
      model: editForm.value.model,
      manufacturer: editForm.value.manufacturer,
      specification: editForm.value.specification,
      surface: editForm.value.surface,
      category: editForm.value.category,
      warehouse_num: editForm.value.warehouse_num,
      total_amount: editForm.value.total_amount,
      unit_per_box: editForm.value.unit_per_box,
      selling_price: editForm.value.selling_price || 0,
      picture: editForm.value.picture || '',
      remark: editForm.value.remark || '',
    };

    const response = await updateInventoryItem(updateData);
    if (response.data.code === 200) {
      ElMessage.success('编辑成功');
      editDialogVisible.value = false;
      await performSearch();
    } else {
      ElMessage.error(response.data.message || '编辑失败');
    }
  } catch (error) {
    console.error('更新库存记录失败:', error);
    ElMessage.error('表单验证失败或编辑失败，请检查输入并重试');
  }
};

// 删除记录（匹配接口 /api/inventory/items/{id}）
const handleDelete = async (row: InventoryItem) => {
  if (!isAdmin) {
    ElMessage.warning('只有管理员才能删除库存记录');
    return;
  }

  try {
    await ElMessageBox.confirm('确定删除此库存记录吗？这个操作不可恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    const response = await deleteInventoryItem(row.id!);
    if (response.data.code === 200) {
      ElMessage.success('删除成功');
      await performSearch();
    } else {
      ElMessage.error(response.data.message || '删除失败');
    }
  } catch (error) {
    if ((error as any).message !== 'cancel') {
      console.error('删除库存记录失败:', error);
      ElMessage.error('删除失败，请稍后重试或联系管理员');
    }
  }
};

// 分页处理器
const handlePageChange = (newPage: number) => {
  page.value = newPage;
  performSearch();
};

const handleSizeChange = (newSize: number) => {
  size.value = newSize;
  page.value = 1; // 重置到第一页
  performSearch();
};

// 重置搜索条件
const resetSearch = () => {
  category.value = null;
  surface.value = null;
  page.value = 1;
};

// 图片预览
const handleImagePreview = (url: string) => {
  previewImageUrl.value = url;
  imagePreviewVisible.value = true;
};

// 图片上传前的检查
const beforeImageUpload = (file: File) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png';
  const isLt2M = file.size / 1024 / 1024 < 2;

  if (!isJPG) {
    ElMessage.error('上传图片只能是 JPG/PNG 格式!');
    return false;
  }
  if (!isLt2M) {
    ElMessage.error('上传图片大小不能超过 2MB!');
    return false;
  }
  return true;
};

// 处理图片上传
const handleImageUpload = async (options: any) => {
  const { file } = options;
  
  if (!beforeImageUpload(file)) {
    return;
  }

  if (!editForm.value.id) {
    ElMessage.error('请先保存商品信息后再上传图片');
    return;
  }

  uploadLoading.value = true;
  try {
    const response = await uploadImage(file, editForm.value.id);
    const result = response as any;
    
    // 检查是否是直接返回URL格式 {url: "..."}
    if (result.data && result.data.url) {
      editForm.value.picture = result.data.url;
      ElMessage.success('图片上传成功');
    } 
    // 检查是否是标准格式 {code: 200, data: {url: "..."}}
    else if (result.data.code === 200 && result.data.data && result.data.data.url) {
      editForm.value.picture = result.data.data.url;
      ElMessage.success('图片上传成功');
    } else {
      ElMessage.error(result.data.message || '图片上传失败');
    }
  } catch (error) {
    console.error('图片上传失败:', error);
    ElMessage.error('图片上传失败');
  } finally {
    uploadLoading.value = false;
  }
};

// 删除图片
const handleImageRemove = () => {
  editForm.value.picture = '';
  ElMessage.success('图片已移除');
};

// 初始加载数据
performSearch();
</script>

<template>
  <div class="inventory-query-container">
    <h1>库存查询</h1>
    <el-divider />

    <div class="header-container">
      <div class="options-section">
        <div class="options-column">
          <div class="option-group">
            <div class="label">产品分类：</div>
            <el-radio-group v-model="category">
              <el-radio :label="null" class="radio-item">全部</el-radio>
              <el-radio
                  v-for="item in categoryOptions"
                  :key="item.value"
                  :label="item.value"
                  class="radio-item"
              >
                {{ item.label }}
              </el-radio>
            </el-radio-group>
          </div>
          <div class="option-group">
            <div class="label">表面处理：</div>
            <el-radio-group v-model="surface">
              <el-radio :label="null" class="radio-item">全部</el-radio>
              <el-radio
                  v-for="item in surfaceOptions"
                  :key="item.value"
                  :label="item.value"
                  class="radio-item"
              >
                {{ item.label }}
              </el-radio>
            </el-radio-group>
          </div>
        </div>
      </div>
      <div class="button-section">
        <el-button type="default" @click="resetSearch">重置</el-button>
        <el-button type="primary" :loading="loading" @click="performSearch">
          搜索
        </el-button>
      </div>
    </div>
    <el-divider />

    <!-- 搜索结果 -->
    <div class="results">
      <el-table
          v-loading="loading"
          :data="searchResults"
          style="width: 100%"
          border
          max-height="600"
      >
        <el-table-column prop="id" label="ID" width="80" fixed />
        <el-table-column prop="model" label="产品型号" width="120" fixed />
        <el-table-column prop="manufacturer" label="制造厂商" width="120" />
        <el-table-column prop="specification" label="规格" width="120" />
        <el-table-column prop="surface" label="表面处理" width="120">
          <template #default="{ row }">
            {{ surfaceOptions.find(opt => opt.value === row.surface)?.label || '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            {{ categoryOptions.find(opt => opt.value === row.category)?.label || '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="warehouse_num" label="仓库编码" width="100" />
        <el-table-column prop="total_amount" label="总数量" width="120">
          <template #default="{ row }">
            {{ row.total_amount }}{{ getUnitLabel(row.category) }}
          </template>
        </el-table-column>
        <el-table-column prop="unit_per_box" label="每箱数量" width="120">
          <template #default="{ row }">
            {{ row.unit_per_box }}{{ getUnitLabel(row.category) }}/箱
          </template>
        </el-table-column>
        <el-table-column label="总箱数" width="150">
          <template #default="{ row }">
            {{ calculateTotalBoxes(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="selling_price" label="销售单价" width="120">
          <template #default="{ row }">
            ¥{{ row.selling_price?.toFixed(2) || '0.00' }}
          </template>
        </el-table-column>
        <el-table-column label="商品图片" width="120">
          <template #default="{ row }">
            <div v-if="row.picture" class="image-container">
              <el-image
                :src="row.picture"
                fit="cover"
                class="table-image"
                :preview-disabled="true"
              />
            </div>
            <span v-else class="no-image">暂无图片</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column label="操作" width="200" fixed="right">
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
    </div>

    <!-- 分页 -->
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

      <!-- 编辑对话框 -->
    <el-dialog
        v-model="editDialogVisible"
        title="编辑库存记录"
        width="50%"
        :close-on-click-modal="false"
    >
      <el-form
          ref="formRef"
          :model="editForm"
          :rules="formRules"
          label-width="120px"
      >
        <el-form-item label="产品型号" prop="model">
          <el-input v-model="editForm.model" />
          </el-form-item>
          <el-form-item label="制造厂商" prop="manufacturer">
            <el-input v-model="editForm.manufacturer" />
          </el-form-item>
          <el-form-item label="规格" prop="specification">
          <el-input v-model="editForm.specification" />
          </el-form-item>
          <el-form-item label="表面处理" prop="surface">
            <el-select v-model="editForm.surface" placeholder="请选择表面处理">
              <el-option
                  v-for="item in surfaceOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="分类" prop="category">
            <el-select v-model="editForm.category" placeholder="请选择分类">
              <el-option
                  v-for="item in categoryOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="仓库编码" prop="warehouse_num">
          <el-input-number v-model="editForm.warehouse_num" :min="1" />
          </el-form-item>
        <el-form-item :label="totalLabel" prop="total_amount">
          <el-input-number v-model="editForm.total_amount" :min="0" />
          </el-form-item>
        <el-form-item :label="boxLabel" prop="unit_per_box">
          <el-input-number v-model="editForm.unit_per_box" :min="1" />
        </el-form-item>
        <el-form-item label="销售单价" prop="selling_price">
          <el-input-number v-model="editForm.selling_price" :precision="2" :min="0" />
        </el-form-item>
        <el-form-item label="商品图片" prop="picture">
          <div class="image-upload-container">
            <div v-if="editForm.picture" class="current-image">
              <el-image
                :src="editForm.picture"
                fit="cover"
                class="edit-image"
              />
              <div class="image-actions">
                <el-button
                  size="small"
                  type="info"
                  :icon="ZoomIn"
                  @click="handleImagePreview(editForm.picture)"
                >
                  预览
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleImageRemove"
                >
                  删除
                </el-button>
              </div>
            </div>
            <el-upload
              class="image-uploader"
              :show-file-list="false"
              :http-request="handleImageUpload"
              :before-upload="beforeImageUpload"
              accept="image/jpeg,image/png"
            >
              <el-button 
                type="primary" 
                :icon="Plus" 
                :loading="uploadLoading"
                v-if="!editForm.picture"
              >
                上传图片
              </el-button>
              <el-button 
                type="warning" 
                :icon="Plus" 
                :loading="uploadLoading"
                v-else
              >
                更换图片
              </el-button>
            </el-upload>
            <div class="upload-tip">
              <el-text size="small" type="info">
                支持 JPG、PNG 格式，文件大小不超过 2MB
              </el-text>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
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

      <!-- 图片预览对话框 -->
      <el-dialog v-model="imagePreviewVisible" title="图片预览" width="50%">
        <div class="image-preview-container">
          <el-image
            :src="previewImageUrl"
            fit="contain"
            style="width: 100%; max-height: 500px;"
          />
        </div>
      </el-dialog>
  </div>
</template>

<style scoped>
.inventory-query-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
}

.options-section {
  flex: 1;
}

.options-column {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.label {
  font-weight: bold;
  min-width: 100px;
  color: #333;
}

.radio-item {
  margin-right: 20px;
}

.button-section {
  display: flex;
  gap: 10px;
}

.results {
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

/* 图片相关样式 */
.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.table-image {
  width: 60px;
  height: 60px;
  border-radius: 4px;
}

.no-image {
  color: #999;
  font-size: 12px;
}

.image-upload-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.current-image {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background-color: #fafafa;
}

.edit-image {
  width: 80px;
  height: 80px;
  border-radius: 4px;
}

.image-actions {
  display: flex;
  gap: 8px;
}

.image-uploader {
  display: flex;
  justify-content: center;
}

.upload-tip {
  text-align: center;
  margin-top: 5px;
}

.image-preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>