<!--订单列表-->
<!--订单列表-->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { getOrders, getOrderDetail, updateOrder, updateOrderItem, deleteOrder, updateDispatchStatus, dispatchOrder, addOrderItem, deleteOrderItem } from '@/api/order';
import { useUserStore } from '@/stores/user';
import { getInventoryByModelNumber } from '@/api/inventory';
import type { OrderQueryParams, Order, SubOrderItem } from '@/types/interfaces';

// 获取用户信息
const userStore = useUserStore();
const operatorId = userStore.getUserInfo()?.id;

// 检查是否为admin角色
const isAdmin = computed(() => {
  const user = userStore.getUserInfo();
  return user?.role_id === 1; // 假设role_id为1是管理员
});

// 使用全局类型定义

const router = useRouter();

// 订单记录
const orderListData = ref<Order[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const searchDateRange = ref<[Date, Date] | []>([]);
const searchPhone = ref<string>('');

// 订单详情对话框控制
const detailDialogVisible = ref(false);
const currentOrderDetail = ref<Order | null>(null);
const orderItemsLoading = ref(false);

// 编辑订单对话框
const editOrderDialogVisible = ref(false);
const editOrderForm = ref<Partial<Order>>({
  id: 0,
  customer_phone: '',
  operator_id: 0,
  remark: ''
});

// 编辑订单项对话框
const editOrderItemDialogVisible = ref(false);
const currentEditItem = ref<SubOrderItem | null>(null);
const editItemForm = ref({
  id: 0,
  quantity: 0,
  price_per_piece: 0,
  subtotal: 0,
  original_subtotal: 0,
  price_difference: 0
});

// 添加订单项对话框
const addOrderItemDialogVisible = ref(false);
const addItemForm = ref({
  order_id: 0,
  item_id: null as number | null,
  model_number: '',
  quantity: null as number | null,
  price_per_piece: null as number | null,
  subtotal: 0,
  original_subtotal: 0,
  price_difference: 0,
  total_pieces: undefined as number | undefined,
  source_warehouse: 1
});

// 日期选择器选项
const pickerOptions = {
  shortcuts: [
    {
      text: '最近一周',
      onClick(picker: any) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
        picker.$emit('pick', [start, end]);
      },
    },
    {
      text: '最近一个月',
      onClick(picker: any) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
        picker.$emit('pick', [start, end]);
      },
    },
    {
      text: '最近三个月',
      onClick(picker: any) {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
        picker.$emit('pick', [start, end]);
      },
    },
  ],
};

// 添加排序方法
const sortOrderList = (list: Order[]) => {
  return [...list].sort((a, b) => {
    const idA = a.id || 0;
    const idB = b.id || 0;
    return idB - idA; // 降序排序
  });
};

// 获取订单列表
const fetchOrderList = async () => {
  try {
    const params: OrderQueryParams = {
      current: page.value,
      size: size.value
    };

    // 应用手机号筛选
    if (searchPhone.value.trim()) {
      params.customer_phone = searchPhone.value.trim();
    }

    // 应用日期筛选
    if (searchDateRange.value && searchDateRange.value.length === 2) {
      const [startDate, endDate] = searchDateRange.value;
      if (startDate && endDate) {
        params.start_time = formatDate(startDate);
        params.end_time = formatDate(endDate, true);
      }
    }

    const result = await getOrders(params);
    if (result.data.code === 200 && result.data.data) {
      const data = result.data.data;
      // 对数据进行排序
      orderListData.value = sortOrderList(data.records || []);
      total.value = data.total || 0;
    } else {
      ElMessage.error('获取订单列表失败');
    }
  } catch (error) {
    console.error('获取订单列表出错:', error);
    ElMessage.error('获取订单列表出错');
  }
};

// 格式化日期
const formatDate = (date: Date, isEndDate = false) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  if (isEndDate) {
    return `${year}-${month}-${day} 23:59:59`;
  }
  return `${year}-${month}-${day} 00:00:00`;
};

// 查看订单详情
const handleViewDetail = async (order: Order) => {
  try {
    orderItemsLoading.value = true;
    const result = await getOrderDetail(order.id);

    if (result.data.code === 200 && result.data.data) {
      currentOrderDetail.value = result.data.data;
      detailDialogVisible.value = true;
    } else {
      ElMessage.error('获取订单详情失败');
    }
  } catch (error) {
    console.error('获取订单详情出错:', error);
    ElMessage.error('获取订单详情出错');
  } finally {
    orderItemsLoading.value = false;
  }
};



// 编辑订单基本信息
const handleEditOrder = (order: Order) => {
  editOrderForm.value = {
    id: order.id,
    customer_phone: order.customer_phone,
    operator_id: operatorId,
    remark: order.remark || ''
  };
  editOrderDialogVisible.value = true;
};

// 保存订单基本信息
const saveOrderEdit = async () => {
  if (!editOrderForm.value.id) {
    ElMessage.error('订单ID不能为空');
    return;
  }

  if (!editOrderForm.value.customer_phone) {
    ElMessage.error('客户手机号不能为空');
    return;
  }

  try {
    const orderData = {
      id: editOrderForm.value.id,
      customer_phone: editOrderForm.value.customer_phone,
      remark: editOrderForm.value.remark
    };

    const response = await updateOrder(orderData);

    if (response.data && response.data.code === 200) {
      ElMessage.success('订单基本信息更新成功');
      editOrderDialogVisible.value = false;
      fetchOrderList();
    } else {
      ElMessage.error(response.data?.message || '更新订单信息失败');
    }
  } catch (error) {
    console.error('更新订单信息出错:', error);
    ElMessage.error('更新订单信息出错');
  }
};

// 编辑订单项
const handleEditItem = (item: SubOrderItem) => {
  currentEditItem.value = item;
  editItemForm.value = {
    id: item.id,
    quantity: item.amount,
    price_per_piece: item.subtotal_price / item.amount, // 计算单价
    subtotal: item.subtotal_price,
    original_subtotal: item.subtotal_price,
    price_difference: 0
  };
  editOrderItemDialogVisible.value = true;
};

// 更新小计金额
const updateSubtotal = () => {
  if (editItemForm.value.quantity && editItemForm.value.price_per_piece) {
    // 计算原始小计
    editItemForm.value.original_subtotal = Number((editItemForm.value.quantity * editItemForm.value.price_per_piece).toFixed(2));
    // 如果还没有手动修改过小计，则使用原始小计
    if (!editItemForm.value.subtotal) {
      editItemForm.value.subtotal = editItemForm.value.original_subtotal;
    }
    // 计算差价
    editItemForm.value.price_difference = Number((editItemForm.value.subtotal - editItemForm.value.original_subtotal).toFixed(2));
  }
};

// 监听小计变化
const handleSubtotalChange = () => {
  if (editItemForm.value.subtotal !== null && editItemForm.value.original_subtotal !== null) {
    editItemForm.value.price_difference = Number((editItemForm.value.subtotal - editItemForm.value.original_subtotal).toFixed(2));
  }
};

// 保存订单项编辑
const saveItemEdit = async () => {
  if (!currentEditItem.value) {
    ElMessage.error('获取订单项信息失败');
    return;
  }

  if (!editItemForm.value.quantity || editItemForm.value.quantity <= 0) {
    ElMessage.error('数量必须大于0');
    return;
  }

  if (!editItemForm.value.price_per_piece || editItemForm.value.price_per_piece <= 0) {
    ElMessage.error('单价必须大于0');
    return;
  }

  try {
    const itemData = {
      id: editItemForm.value.id,
      amount: editItemForm.value.quantity,
      subtotal_price: editItemForm.value.subtotal,
      change_type: 0 // 修改操作
    };

    const response = await updateOrderItem(itemData);

    if (response.data && response.data.code === 200) {
      ElMessage.success('订单项更新成功');
      editOrderItemDialogVisible.value = false;

      // 如果当前有打开的订单详情，重新获取并刷新它
      if (currentOrderDetail.value && currentOrderDetail.value.id) {
        handleViewDetail({id: currentOrderDetail.value.id} as Order);
      }

      fetchOrderList();
    } else {
      ElMessage.error(response.data?.message || '更新订单项失败');
    }
  } catch (error) {
    console.error('更新订单项出错:', error);
    ElMessage.error('更新订单项出错');
  }
};

// 新增子订单项对话框
const addSubOrderItemDialogVisible = ref(false);
const addSubOrderItemForm = ref({
  item_id: null as number | null,
  amount: null as number | null,
  subtotal_price: null as number | null
});

// 处理新增子订单项
const handleAddSubOrderItem = () => {
  if (!currentOrderDetail.value) {
    ElMessage.error('请先选择订单');
    return;
  }
  
  addSubOrderItemForm.value = {
    item_id: null,
    amount: null,
    subtotal_price: null
  };
  addSubOrderItemDialogVisible.value = true;
};

// 保存新增的子订单项
const saveAddSubOrderItem = async () => {
  if (!currentOrderDetail.value) {
    ElMessage.error('订单信息不存在');
    return;
  }

  if (!addSubOrderItemForm.value.item_id) {
    ElMessage.error('商品ID不能为空');
    return;
  }

  if (!addSubOrderItemForm.value.amount || addSubOrderItemForm.value.amount <= 0) {
    ElMessage.error('数量必须大于0');
    return;
  }

  if (!addSubOrderItemForm.value.subtotal_price || addSubOrderItemForm.value.subtotal_price <= 0) {
    ElMessage.error('小计金额必须大于0');
    return;
  }

  try {
    const itemData = {
      id: 0, // 新增时子订单项ID为0，由后端生成
      order_id: currentOrderDetail.value.id, // 母订单ID
      item_id: addSubOrderItemForm.value.item_id, // 商品ID
      amount: addSubOrderItemForm.value.amount,
      subtotal_price: addSubOrderItemForm.value.subtotal_price,
      change_type: 1 // 新增操作
    };

    const response = await updateOrderItem(itemData);

    if (response.data && response.data.code === 200) {
      ElMessage.success('新增子订单项成功');
      addSubOrderItemDialogVisible.value = false;

      // 重新获取订单详情
      if (currentOrderDetail.value && currentOrderDetail.value.id) {
        handleViewDetail({id: currentOrderDetail.value.id} as Order);
      }

      fetchOrderList();
    } else {
      ElMessage.error(response.data?.message || '新增子订单项失败');
    }
  } catch (error) {
    console.error('新增子订单项出错:', error);
    ElMessage.error('新增子订单项出错');
  }
};

// 删除子订单项
const handleDeleteSubOrderItem = (item: SubOrderItem) => {
  if (!currentOrderDetail.value) {
    ElMessage.error('订单信息不存在');
    return;
  }

  ElMessageBox.confirm('确定删除此子订单项吗？删除后不可恢复。', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const itemData = {
        id: item.id,
        order_id: currentOrderDetail.value!.id, // 母订单ID
        item_id: item.item_id, // 商品ID
        amount: 0, // 删除时可以设为0
        subtotal_price: 0, // 删除时可以设为0
        change_type: 2 // 删除操作
      };

      const response = await updateOrderItem(itemData);

      if (response.data && response.data.code === 200) {
        ElMessage.success('子订单项删除成功');

        // 重新获取订单详情
        if (currentOrderDetail.value && currentOrderDetail.value.id) {
          handleViewDetail({id: currentOrderDetail.value.id} as Order);
        }

        fetchOrderList();
      } else {
        ElMessage.error(response.data?.message || '删除子订单项失败');
      }
    } catch (error) {
      console.error('删除子订单项出错:', error);
      ElMessage.error('删除子订单项出错');
    }
  }).catch(() => {
    // 取消删除
  });
};

// 监听产品型号变化
const handleModelNumberChange = async () => {
  if (addItemForm.value.model_number) {
    try {
      const result = await getInventoryByModelNumber(addItemForm.value.model_number);
      if (result.data.code === 200 && result.data.data) {
        const inventoryData = result.data.data;
        // 根据新接口返回的数据结构进行映射
        addItemForm.value.item_id = inventoryData.id; // 使用id而不是item_id
        addItemForm.value.total_pieces = inventoryData.total_amount; // 使用total_amount而不是total_pieces
        ElMessage.success('已自动填充商品ID和库存数量');
      } else {
        ElMessage.warning('未找到对应的库存信息');
        addItemForm.value.item_id = null;
        addItemForm.value.total_pieces = undefined;
      }
    } catch (error) {
      console.error('获取库存信息失败:', error);
      ElMessage.error('获取库存信息失败');
      addItemForm.value.item_id = null;
      addItemForm.value.total_pieces = undefined;
    }
  }
};

// 添加订单项
const handleAddItem = (order: Order) => {
  addItemForm.value = {
    order_id: order.id,
    item_id: null,
    model_number: '',
    quantity: null,
    price_per_piece: null,
    subtotal: 0,
    original_subtotal: 0,
    price_difference: 0,
    total_pieces: undefined,
    source_warehouse: 1
  };
  addOrderItemDialogVisible.value = true;
};

// 更新添加项的小计金额
const updateAddItemSubtotal = () => {
  if (addItemForm.value.quantity && addItemForm.value.price_per_piece) {
    // 计算小计
    const calculatedSubtotal = Number((addItemForm.value.quantity * addItemForm.value.price_per_piece).toFixed(2));
    addItemForm.value.subtotal = calculatedSubtotal;
    addItemForm.value.original_subtotal = calculatedSubtotal;
    // 重置差价
    addItemForm.value.price_difference = 0;
  }
};

// 监听添加项小计变化
const handleAddItemSubtotalChange = () => {
  if (addItemForm.value.subtotal !== null && addItemForm.value.original_subtotal !== null) {
    // 只有当手动输入的小计与原始计算的小计不同时，才计算并显示差价
    if (addItemForm.value.subtotal !== addItemForm.value.original_subtotal) {
      addItemForm.value.price_difference = Number((addItemForm.value.subtotal - addItemForm.value.original_subtotal).toFixed(2));
    } else {
      addItemForm.value.price_difference = 0;
    }
  }
};

// 保存新添加的订单项
const saveAddItem = async () => {
  if (!addItemForm.value.order_id) {
    ElMessage.error('订单ID不能为空');
    return;
  }

  if (!addItemForm.value.item_id) {
    ElMessage.error('库存商品ID不能为空');
    return;
  }

  if (!addItemForm.value.model_number) {
    ElMessage.error('产品型号不能为空');
    return;
  }

  if (!addItemForm.value.quantity || addItemForm.value.quantity <= 0) {
    ElMessage.error('数量必须大于0');
    return;
  }

  if (!addItemForm.value.price_per_piece || addItemForm.value.price_per_piece <= 0) {
    ElMessage.error('单价必须大于0');
    return;
  }

  try {
    const orderId = addItemForm.value.order_id;
    const itemData = {
      item_id: addItemForm.value.item_id,
      model_number: addItemForm.value.model_number,
      quantity: addItemForm.value.quantity,
      price_per_piece: addItemForm.value.price_per_piece,
      subtotal: addItemForm.value.subtotal
    };

    const response = await addOrderItem(orderId, itemData);

    if (response.data && response.data.code === 200) {
      ElMessage.success('添加订单项成功');
      addOrderItemDialogVisible.value = false;

      // 如果当前有打开的订单详情，重新获取并刷新它
      if (currentOrderDetail.value && currentOrderDetail.value.id === orderId) {
        handleViewDetail({id: orderId} as Order);
      }

      fetchOrderList();
    } else {
      ElMessage.error(response.data?.message || '添加订单项失败');
    }
  } catch (error) {
    console.error('添加订单项出错:', error);
    ElMessage.error('添加订单项出错');
  }
};

// 删除订单项
const handleDeleteItem = (item: SubOrderItem) => {
  ElMessageBox.confirm('确定删除此订单项吗？删除后不可恢复。', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const response = await deleteOrderItem(item.id);

      if (response.data && response.data.code === 200) {
        ElMessage.success('订单项删除成功');

        // 如果当前有打开的订单详情，重新获取并刷新它
        if (currentOrderDetail.value && currentOrderDetail.value.id === item.order_id) {
          handleViewDetail({id: item.order_id} as Order);
        }

        fetchOrderList();
      } else {
        ElMessage.error(response.data?.message || '删除订单项失败');
      }
    } catch (error) {
      console.error('删除订单项出错:', error);
      ElMessage.error('删除订单项出错');
    }
  }).catch(() => {
    // 取消删除
  });
};

// 删除整个订单
const handleDeleteOrder = (orderId: number) => {
  ElMessageBox.confirm('确定删除此订单及其所有商品项吗？删除后不可恢复。', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const response = await deleteOrder(orderId);

      if (response.data && response.data.code === 200) {
        ElMessage.success('订单删除成功');
        fetchOrderList();
      } else {
        ElMessage.error(response.data?.message || '删除订单失败');
      }
    } catch (error) {
      console.error('删除订单出错:', error);
      ElMessage.error('删除订单出错');
    }
  }).catch(() => {
    // 取消删除
  });
};

// 分页处理
const handlePageChange = (newPage: number) => {
  page.value = newPage;
  fetchOrderList();
};

const handleSizeChange = (newSize: number) => {
  size.value = newSize;
  page.value = 1;
  fetchOrderList();
};

// 清除筛选条件
const clearFilter = () => {
  searchDateRange.value = [];
  searchPhone.value = '';
  page.value = 1;
  fetchOrderList();
};

// 计算商品数量
const getItemsCount = (order: Order) => {
  return order.sub_order_count || 0;
};



// 派送状态映射
const dispatchStatusMap = {
  0: { text: '未派送', type: 'info' },
  1: { text: '待接单', type: 'warning' },
  2: { text: '配送中', type: 'primary' },
  3: { text: '已完成', type: 'success' },
  4: { text: '已取消', type: 'danger' }
};

// 获取派送状态文本
const getDispatchStatusText = (status: number | undefined) => {
  if (status === undefined) return '未派送';
  return dispatchStatusMap[status as keyof typeof dispatchStatusMap]?.text || '未知状态';
};

// 获取派送状态类型（用于标签颜色）
const getDispatchStatusType = (status: number | undefined) => {
  if (status === undefined) return 'info';
  return dispatchStatusMap[status as keyof typeof dispatchStatusMap]?.type || '';
};

// 派送对话框
const dispatchDialogVisible = ref(false);
const currentDispatchOrder = ref<Order | null>(null);
const dispatchForm = ref({
  orderId: 0,
  deliveryAddress: '',
  deliveryRemark: '',
  deliveryWeight: 0,
  deliveryFee: 0,
});



// 处理派送按钮点击
const handleDispatchClick = (order: Order) => {
  currentDispatchOrder.value = order;
  dispatchForm.value = {
    orderId: order.id,
    deliveryAddress: order.delivery_address || '',
    deliveryRemark: '',
    deliveryWeight: 0,
    deliveryFee: 0,
  };
  dispatchDialogVisible.value = true;
};

// 提交派送请求
const handleDispatch = async () => {
  if (!dispatchForm.value.deliveryAddress.trim()) {
    ElMessage.error('派送地址不能为空');
    return;
  }

  if (dispatchForm.value.deliveryFee < 0) {
    ElMessage.error('配送费不能为负数');
    return;
  }

  try {
    // 使用 ElMessageBox 确认派送操作
    await ElMessageBox.confirm('确认派送该订单?', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    // 用户确认后继续
    try {
      // 1. 首先更新8080的订单状态 (设置为已派送状态：1)
      const updateResult = await updateDispatchStatus(currentDispatchOrder.value?.id || 0, 1);
      
      if (updateResult.data && updateResult.data.code === 200) {
        // 2. 然后向配送系统发送派送请求 - 使用蛇形命名
        const dispatchData = {
          id: currentDispatchOrder.value?.id || 0,
          customer_phone: currentDispatchOrder.value?.customer_phone || '',
          delivery_address: dispatchForm.value.deliveryAddress,
          order_no: currentDispatchOrder.value?.order_no || '',
          delivery_fee: dispatchForm.value.deliveryFee,
          goods_weight: dispatchForm.value.deliveryWeight,
          remark: dispatchForm.value.deliveryRemark
        };
        
        const response = await dispatchOrder(dispatchData);
        
        if (response.data && response.data.code === 200) {
          ElMessage.success('订单派送成功');
          dispatchDialogVisible.value = false;
          fetchOrderList(); // 重新加载列表
        } else {
          throw new Error(response.data?.message || '派送订单失败');
        }
      } else {
        throw new Error(updateResult.data?.message || '更新派送状态失败');
      }
    } catch (error) {
      console.error('派送订单时出错:', error);
      ElMessage.error('派送处理失败');
    }
  } catch (error) {
    // 用户取消确认
    ElMessage.info('已取消派送操作');
  }
};

// 初始化
onMounted(() => {
  fetchOrderList();
});
</script>

<template>
  <h1>订单管理</h1>
  <hr>
  <div class="records-container">
    <!-- 搜索区域 -->
    <el-row :gutter="20" class="search-section">
      <el-col :span="8">
        <el-form-item label="按日期筛选">
          <el-date-picker
              v-model="searchDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :picker-options="pickerOptions"
              @change="fetchOrderList"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="按手机号筛选">
          <el-input
              v-model="searchPhone"
              placeholder="输入客户手机号"
              clearable
              @input="fetchOrderList"
          />
        </el-form-item>
      </el-col>
      <el-col :span="4">
        <el-button @click="clearFilter">清除筛选</el-button>
      </el-col>
    </el-row>

    <!-- 订单列表 -->
    <el-table
        v-if="orderListData.length > 0"
        :data="orderListData"
        style="width: 100%"
        border
    >
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="order_no" label="订单编号" width="150" />
      <el-table-column prop="customer_phone" label="客户手机号" width="120" />
      <el-table-column label="商品数量" width="90">
        <template #default="{ row }">
          {{ getItemsCount(row) }}
        </template>
      </el-table-column>
      <el-table-column prop="total_price" label="订单总金额" width="120">
        <template #default="{ row }">
          {{ row.total_price.toFixed(2) }} 元
        </template>
      </el-table-column>
      <el-table-column prop="adjusted_amount" label="调整后金额" width="120">
        <template #default="{ row }">
          {{ row.adjusted_amount ? row.adjusted_amount.toFixed(2) + ' 元' : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="订单备注" min-width="150" :show-overflow-tooltip="true" />
      <el-table-column prop="create_time" label="创建时间" width="160">
        <template #default="{ row }">
          {{ row.create_time ? new Date(row.create_time).toLocaleString() : '-' }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="140" fixed="right">
        <template #default="scope">
          <div class="button-group-vertical">
            <div class="button-row">
              <el-button type="primary" size="small" @click="handleViewDetail(scope.row)">详情</el-button>
              <el-button type="warning" size="small" @click="handleEditOrder(scope.row)">编辑</el-button>
            </div>
            <div class="button-row">
              <el-button 
                v-if="!scope.row.dispatch_status || scope.row.dispatch_status === 0"
                type="primary" 
                size="small" 
                @click="handleDispatchClick(scope.row)"
              >派送</el-button>
            </div>
            <div v-if="isAdmin" class="button-row">
              <el-popconfirm
                title="确定要删除这个订单吗？"
                @confirm="handleDeleteOrder(scope.row.id)"
              >
                <template #reference>
                  <el-button type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div v-else class="no-data">暂无订单记录</div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
          v-if="orderListData.length > 0"
          :current-page="page"
          :page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
      />
    </div>

    <!-- 订单详情对话框 -->
    <el-dialog
        v-model="detailDialogVisible"
        title="订单详情"
        width="80%"
        destroy-on-close
    >
      <div v-if="currentOrderDetail" class="order-detail">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="订单ID">{{ currentOrderDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="订单编号">{{ currentOrderDetail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="客户手机号">{{ currentOrderDetail.customer_phone }}</el-descriptions-item>
          <el-descriptions-item label="订单总金额">{{ currentOrderDetail.total_price ? currentOrderDetail.total_price.toFixed(2) + ' 元' : '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ currentOrderDetail.create_time ? new Date(currentOrderDetail.create_time).toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ currentOrderDetail.update_time ? new Date(currentOrderDetail.update_time).toLocaleString() : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="订单备注" :span="2">
            {{ currentOrderDetail.remark || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="order-items-header">
          <h3>订单商品 ({{ currentOrderDetail.sub_order?.length || 0 }}项)</h3>
          <el-button type="primary" size="small" @click="handleAddSubOrderItem">新增商品</el-button>
        </div>

        <el-table
            v-loading="orderItemsLoading"
            :data="currentOrderDetail.sub_order || []"
            border
            style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="item_id" label="商品ID" width="100" />
          <el-table-column prop="amount" label="数量" width="100" />
          <el-table-column prop="subtotal_price" label="小计" width="120">
            <template #default="{ row }">
              {{ row.subtotal_price.toFixed(2) }} 元
            </template>
          </el-table-column>
          <el-table-column prop="create_time" label="创建时间" width="180">
            <template #default="{ row }">
              {{ row.create_time ? new Date(row.create_time).toLocaleString() : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <div class="button-row">
                <el-button type="warning" size="small" @click="handleEditItem(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="handleDeleteSubOrderItem(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 编辑订单基本信息对话框 -->
    <el-dialog
        v-model="editOrderDialogVisible"
        title="编辑订单基本信息"
        width="40%"
        destroy-on-close
    >
      <el-form :model="editOrderForm" label-width="120px">
        <el-form-item label="客户手机号" required>
          <el-input
              v-model="editOrderForm.customer_phone"
              placeholder="请输入客户手机号"
              maxlength="11"
          />
        </el-form-item>
        <el-form-item label="操作人ID" required>
          <el-input
              v-model.number="editOrderForm.operator_id"
              placeholder="系统自动获取"
              type="number"
              disabled
          />
        </el-form-item>
        <el-form-item label="订单备注">
          <el-input
              v-model="editOrderForm.remark"
              type="textarea"
              :rows="3"
              placeholder="请输入订单备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editOrderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveOrderEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑订单项对话框 -->
    <el-dialog
        v-model="editOrderItemDialogVisible"
        title="编辑订单商品"
        width="40%"
        destroy-on-close
    >
      <div v-if="currentEditItem" class="item-info">
        <div class="info-row">
          <span class="label">订单项ID:</span>
          <span class="value">{{ currentEditItem.id }}</span>
        </div>
        <div class="info-row">
          <span class="label">商品ID:</span>
          <span class="value">{{ currentEditItem.item_id }}</span>
        </div>
        <div class="info-row">
          <span class="label">订单ID:</span>
          <span class="value">{{ currentEditItem.order_id }}</span>
        </div>
      </div>

      <el-divider></el-divider>

      <el-form :model="editItemForm" label-width="120px">
        <el-form-item label="数量" required>
          <el-input
              v-model.number="editItemForm.quantity"
              placeholder="请输入数量"
              type="number"
              :min="1"
              @input="updateSubtotal"
          />
        </el-form-item>
        <el-form-item label="单价" required>
          <el-input
              v-model.number="editItemForm.price_per_piece"
              placeholder="请输入单价"
              type="number"
              :min="0.01"
              :step="0.01"
              @input="updateSubtotal"
          />
        </el-form-item>
        <el-form-item label="小计">
          <el-input
              v-model.number="editItemForm.subtotal"
              placeholder="请输入小计金额"
              type="number"
              :min="0"
              :step="0.01"
              @input="handleSubtotalChange"
          />
        </el-form-item>
        <div v-if="editItemForm.price_difference !== 0" class="price-difference-info">
          <span :class="{ 
            'price-difference': true,
            'positive': editItemForm.price_difference > 0,
            'negative': editItemForm.price_difference < 0
          }">
            差价: {{ editItemForm.price_difference > 0 ? '+' : '' }}{{ editItemForm.price_difference.toFixed(2) }} 元
          </span>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="editOrderItemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItemEdit">保存</el-button>
      </template>
    </el-dialog>



    <!-- 派送对话框 -->
    <el-dialog
      v-model="dispatchDialogVisible"
      title="派送订单"
      width="50%"
      destroy-on-close
    >
      <div v-if="currentDispatchOrder" class="order-info-summary">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单编号">{{ currentDispatchOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="客户手机号">{{ currentDispatchOrder.customer_phone }}</el-descriptions-item>
          <el-descriptions-item label="订单总金额">
            {{ currentDispatchOrder.total_price ? currentDispatchOrder.total_price.toFixed(2) + ' 元' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ currentDispatchOrder.create_time ? new Date(currentDispatchOrder.create_time).toLocaleString() : '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <!-- 派送表单 -->
      <el-form :model="dispatchForm" label-width="120px">
        <el-form-item label="配送地址" required>
          <el-input
            v-model="dispatchForm.deliveryAddress"
            placeholder="请输入配送地址"
          />
        </el-form-item>
        <el-form-item label="配送备注">
          <el-input
            v-model="dispatchForm.deliveryRemark"
            type="textarea"
            placeholder="请输入配送备注"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="货物吨数" required>
          <el-input-number
            v-model="dispatchForm.deliveryWeight"
            :min="0.1"
            :step="0.1"
            :precision="1"
          />
        </el-form-item>
        <el-form-item label="配送费" required>
          <el-input-number
            v-model="dispatchForm.deliveryFee"
            :min="0"
            :step="1"
            :precision="0"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dispatchDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleDispatch">确认派送</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增子订单项对话框 -->
    <el-dialog
        v-model="addSubOrderItemDialogVisible"
        title="新增子订单项"
        width="40%"
        destroy-on-close
    >
      <el-form :model="addSubOrderItemForm" label-width="120px">
        <el-form-item label="商品ID" required>
          <el-input
              v-model.number="addSubOrderItemForm.item_id"
              placeholder="请输入商品ID"
              type="number"
              :min="1"
          />
        </el-form-item>
        <el-form-item label="数量" required>
          <el-input
              v-model.number="addSubOrderItemForm.amount"
              placeholder="请输入数量"
              type="number"
              :min="1"
          />
        </el-form-item>
        <el-form-item label="小计金额" required>
          <el-input
              v-model.number="addSubOrderItemForm.subtotal_price"
              placeholder="请输入小计金额"
              type="number"
              :min="0.01"
              :step="0.01"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addSubOrderItemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAddSubOrderItem">保存</el-button>
      </template>
    </el-dialog>


  </div>
</template>

<style scoped>
.records-container {
  margin-top: 20px;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #666;
}

.search-section {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-bottom: 20px;
}

.order-detail {
  margin-bottom: 20px;
}



.item-info {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 10px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row .label {
  width: 100px;
  color: #606266;
  font-weight: 500;
}

.info-row .value {
  flex: 1;
  color: #303133;
}

.price-difference-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.price-difference {
  color: #f56c6c;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.button-group-vertical {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.button-row {
  display: flex;
  gap: 5px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.no-data {
  text-align: center;
  padding: 30px;
  color: #909399;
}

.order-items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.order-items-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

/* 派送对话框样式 */
.order-info-summary {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}
</style>