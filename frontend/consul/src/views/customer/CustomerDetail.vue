<template>
  <div class="customer-detail-container">
    <el-page-header @back="handleBack" title="返回">
      <template #content>
        <span class="page-title">客户详情</span>
      </template>
    </el-page-header>

    <div v-loading="loading" class="detail-content">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-button
              :type="customerDetail?.base_info.status === 1 ? 'danger' : 'success'"
              size="small"
              @click="handleToggleStatus"
            >
              {{ customerDetail?.base_info.status === 1 ? '停用账号' : '启用账号' }}
            </el-button>
          </div>
        </template>

        <el-descriptions :column="2" border v-if="customerDetail">
          <el-descriptions-item label="ID">
            {{ customerDetail.base_info.id }}
          </el-descriptions-item>
          <el-descriptions-item label="昵称">
            {{ customerDetail.base_info.nickname }}
          </el-descriptions-item>
          <el-descriptions-item label="手机号">
            {{ customerDetail.base_info.phone }}
          </el-descriptions-item>
          <el-descriptions-item label="会员等级">
            <el-tag type="success">{{ customerDetail.base_info.level_name }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="customerDetail.base_info.status === 1 ? 'success' : 'danger'">
              {{ customerDetail.base_info.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="注册渠道">
            {{ customerDetail.base_info.register_channel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="注册时间" :span="2">
            {{ customerDetail.base_info.create_time }}
          </el-descriptions-item>
          <el-descriptions-item label="头像" :span="2">
            <el-avatar :src="customerDetail.base_info.avatar || '/default-avatar.png'" :size="60" />
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 资产信息 -->
      <el-card class="info-card">
        <template #header>
          <span>资产信息</span>
        </template>

        <el-row :gutter="20" v-if="customerDetail">
          <el-col :span="12">
            <el-statistic title="积分余额" :value="customerDetail.assets.points_balance">
              <template #suffix>分</template>
            </el-statistic>
          </el-col>
          <el-col :span="12">
            <el-statistic title="优惠券数量" :value="customerDetail.assets.coupon_count">
              <template #suffix>张</template>
            </el-statistic>
          </el-col>
        </el-row>
      </el-card>

      <!-- 统计信息 -->
      <el-card class="info-card">
        <template #header>
          <span>消费统计</span>
        </template>

        <el-row :gutter="20" v-if="customerDetail">
          <el-col :span="12">
            <el-statistic title="订单总数" :value="customerDetail.stats.total_orders">
              <template #suffix>单</template>
            </el-statistic>
          </el-col>
          <el-col :span="12">
            <el-statistic title="消费总额" :value="customerDetail.stats.total_spent" :precision="2">
              <template #prefix>¥</template>
            </el-statistic>
          </el-col>
        </el-row>
      </el-card>

      <!-- 地址谱 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>
              <el-icon><Location /></el-icon>
              收货地址谱
            </span>
            <el-button type="primary" size="small" @click="handleAddAddress">
              <el-icon><Plus /></el-icon>
              添加地址
            </el-button>
          </div>
        </template>

        <div v-loading="addressLoading">
          <div v-if="addressList.length > 0" class="address-list">
            <div
              v-for="addr in addressList"
              :key="addr.id"
              class="address-item"
              :class="{ 'is-default': addr.is_default === 1 }"
            >
              <div class="address-header">
                <div class="address-tag">
                  <el-tag v-if="addr.tag" size="small" type="info">{{ addr.tag }}</el-tag>
                  <el-tag v-if="addr.is_default === 1" size="small" type="success">默认</el-tag>
                </div>
                <div class="address-actions">
                  <el-button type="primary" link size="small" @click="handleEditAddress(addr)">
                    编辑
                  </el-button>
                  <el-button type="danger" link size="small" @click="handleDeleteAddress(addr)">
                    删除
                  </el-button>
                </div>
              </div>
              <div class="address-content">
                <div class="address-receiver">
                  <span class="receiver-name">{{ addr.receiver_name }}</span>
                  <span class="receiver-phone">{{ addr.receiver_phone }}</span>
                </div>
                <div class="address-detail">
                  {{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无收货地址" />
        </div>
      </el-card>
    </div>

    <!-- 状态变更对话框 -->
    <el-dialog
      v-model="statusDialogVisible"
      :title="customerDetail?.base_info.status === 1 ? '停用客户' : '启用客户'"
      width="400px"
    >
      <el-form :model="statusForm" label-width="80px">
        <el-form-item label="原因" v-if="customerDetail?.base_info.status === 1">
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

    <!-- 地址编辑对话框 -->
    <el-dialog
      v-model="addressDialogVisible"
      :title="isEditingAddress ? '编辑地址' : '添加地址'"
      width="500px"
      @close="handleAddressDialogClose"
    >
      <el-form
        ref="addressFormRef"
        :model="addressForm"
        :rules="addressRules"
        label-width="100px"
      >
        <el-form-item label="收货人" prop="receiver_name">
          <el-input v-model="addressForm.receiver_name" placeholder="请输入收货人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="receiver_phone">
          <el-input v-model="addressForm.receiver_phone" placeholder="请输入联系电话" maxlength="11" />
        </el-form-item>
        <el-form-item label="所在地区" required>
          <el-row :gutter="10">
            <el-col :span="8">
              <el-form-item prop="province" style="margin-bottom: 0">
                <el-input v-model="addressForm.province" placeholder="省" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item prop="city" style="margin-bottom: 0">
                <el-input v-model="addressForm.city" placeholder="市" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item prop="district" style="margin-bottom: 0">
                <el-input v-model="addressForm.district" placeholder="区/县" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="详细地址" prop="detail">
          <el-input
            v-model="addressForm.detail"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址（街道、门牌号等）"
          />
        </el-form-item>
        <el-form-item label="标签" prop="tag">
          <el-radio-group v-model="addressForm.tag">
            <el-radio label="家">家</el-radio>
            <el-radio label="公司">公司</el-radio>
            <el-radio label="工地">工地</el-radio>
            <el-radio label="其他">其他</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="addressForm.is_default" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addressDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddressSubmit" :loading="addressSubmitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { Location, Plus } from '@element-plus/icons-vue';
import {
  getAdminCustomerDetail,
  updateCustomerStatus,
  getCustomerAddresses,
  addCustomerAddress,
  updateCustomerAddress,
  deleteCustomerAddress,
  type CustomerDetailResponse,
  type UpdateCustomerStatusRequest,
  type CustomerAddress
} from '@/api/customer';

const route = useRoute();
const router = useRouter();

const customerId = Number(route.params.id);
const loading = ref(false);
const customerDetail = ref<CustomerDetailResponse | null>(null);

// 状态变更对话框
const statusDialogVisible = ref(false);
const statusForm = reactive<UpdateCustomerStatusRequest>({
  status: 0,
  reason: ''
});
const submitting = ref(false);

// 地址管理相关
const addressLoading = ref(false);
const addressList = ref<CustomerAddress[]>([]);
const addressDialogVisible = ref(false);
const isEditingAddress = ref(false);
const addressSubmitting = ref(false);
const addressFormRef = ref<FormInstance>();

const addressForm = reactive<CustomerAddress>({
  id: 0,
  customer_id: 0,
  receiver_name: '',
  receiver_phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  tag: '家',
  is_default: 0
});

const addressRules: FormRules = {
  receiver_name: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' }
  ],
  receiver_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号', trigger: 'blur' }
  ],
  province: [
    { required: true, message: '请输入省份', trigger: 'blur' }
  ],
  city: [
    { required: true, message: '请输入城市', trigger: 'blur' }
  ],
  district: [
    { required: true, message: '请输入区/县', trigger: 'blur' }
  ],
  detail: [
    { required: true, message: '请输入详细地址', trigger: 'blur' }
  ]
};

// 获取客户详情
const fetchCustomerDetail = async () => {
  loading.value = true;
  try {
    const res = await getAdminCustomerDetail(customerId);
    if (res.data.code === 200 && res.data.data) {
      customerDetail.value = res.data.data;
    } else {
      ElMessage.error(res.data.message || '获取详情失败');
    }
  } catch (error) {
    console.error('获取客户详情失败:', error);
    ElMessage.error('获取详情失败');
  } finally {
    loading.value = false;
  }
};

// 返回
const handleBack = () => {
  router.back();
};

// 切换状态
const handleToggleStatus = () => {
  if (!customerDetail.value) return;
  statusForm.status = customerDetail.value.base_info.status === 1 ? 0 : 1;
  statusForm.reason = '';
  statusDialogVisible.value = true;
};

// 提交状态变更
const handleStatusSubmit = async () => {
  if (!customerDetail.value) return;
  
  submitting.value = true;
  try {
    const res = await updateCustomerStatus(customerId, statusForm);
    if (res.data.code === 200) {
      ElMessage.success('操作成功');
      statusDialogVisible.value = false;
      fetchCustomerDetail();
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

// 获取客户地址列表
const fetchAddressList = async () => {
  if (!customerDetail.value?.base_info.phone) return;
  
  addressLoading.value = true;
  try {
    const res = await getCustomerAddresses(customerDetail.value.base_info.phone);
    if (res.data.code === 200) {
      addressList.value = res.data.data || [];
    } else {
      // 可能是暂无地址，不显示错误
      addressList.value = [];
    }
  } catch (error) {
    console.error('获取地址列表失败:', error);
    addressList.value = [];
  } finally {
    addressLoading.value = false;
  }
};

// 添加地址
const handleAddAddress = () => {
  isEditingAddress.value = false;
  Object.assign(addressForm, {
    id: 0,
    customer_id: customerId,
    receiver_name: '',
    receiver_phone: customerDetail.value?.base_info.phone || '',
    province: '',
    city: '',
    district: '',
    detail: '',
    tag: '家',
    is_default: 0
  });
  addressDialogVisible.value = true;
};

// 编辑地址
const handleEditAddress = (addr: CustomerAddress) => {
  isEditingAddress.value = true;
  Object.assign(addressForm, { ...addr });
  addressDialogVisible.value = true;
};

// 删除地址
const handleDeleteAddress = async (addr: CustomerAddress) => {
  try {
    await ElMessageBox.confirm('确定要删除这个地址吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    const res = await deleteCustomerAddress(addr.id);
    if (res.data.code === 200) {
      ElMessage.success('地址删除成功');
      fetchAddressList();
    } else {
      ElMessage.error(res.data.message || '删除失败');
    }
  } catch (error) {
    // 用户取消或请求失败
    if ((error as any)?.message) {
      ElMessage.error('删除失败');
    }
  }
};

// 地址对话框关闭
const handleAddressDialogClose = () => {
  addressFormRef.value?.resetFields();
};

// 提交地址
const handleAddressSubmit = async () => {
  if (!addressFormRef.value) return;
  
  await addressFormRef.value.validate(async (valid) => {
    if (!valid) return;
    
    addressSubmitting.value = true;
    try {
      let res;
      if (isEditingAddress.value) {
        // 编辑模式 - 调用更新接口
        res = await updateCustomerAddress(addressForm);
      } else {
        // 添加模式 - 调用添加接口
        res = await addCustomerAddress(addressForm);
      }
      
      if (res.data.code === 200) {
        ElMessage.success(isEditingAddress.value ? '地址修改成功' : '地址添加成功');
        addressDialogVisible.value = false;
        fetchAddressList();
      } else {
        ElMessage.error(res.data.message || '操作失败');
      }
    } catch (error) {
      console.error('保存地址失败:', error);
      ElMessage.error('操作失败');
    } finally {
      addressSubmitting.value = false;
    }
  });
};

onMounted(async () => {
  await fetchCustomerDetail();
  fetchAddressList();
});
</script>

<style scoped>
.customer-detail-container {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.detail-content {
  margin-top: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.el-statistic {
  text-align: center;
}

/* 地址列表样式 */
.address-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.address-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  background: #fafafa;
  transition: all 0.3s;
}

.address-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.address-item.is-default {
  border-color: #67c23a;
  background: linear-gradient(135deg, #f0f9eb 0%, #fafafa 100%);
}

.address-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.address-tag {
  display: flex;
  gap: 6px;
}

.address-actions {
  display: flex;
  gap: 5px;
}

.address-content {
  font-size: 14px;
}

.address-receiver {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.receiver-name {
  font-weight: 600;
  color: #303133;
}

.receiver-phone {
  color: #606266;
}

.address-detail {
  color: #606266;
  line-height: 1.5;
}
</style>
