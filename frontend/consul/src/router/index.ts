import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '@/views/Login.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    // 登录页面
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    // 仪表盘及子路由
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue'),
      redirect: '/dashboard/welcome', // 调整 redirect 路径与父路径一致
      children: [
        {
          path: 'order/aftersales/:id?', // Use relative path without leading /
          name: 'order-aftersales',
          component: () => import('@/views/order/OrderAftersales.vue'),
          props: true // This is important to pass route params as props
        },
        {
          path: 'order/list',
          name: 'order-list',
          component: () => import('@/views/order/OrderList.vue'),
        },
        {
          path: 'order/delivery',
          name: 'order-delivery',
          component: () => import('@/views/order/OrderDelivery.vue'),
        },
        // 欢迎页面
        {
          path: 'welcome', // 相对路径，去掉前导斜杠
          name: 'welcome',
          component: () => import('@/views/Welcome.vue'),
        },
        // 仓库管理
        {
          path: 'warehouse/list', // 统一小写连字符
          name: 'warehouse-list', // 使用连字符保持一致
          component: () => import('@/views/warehouse/WarehouseList.vue'), // 组件名规范化
        },
        // 库存管理
        {
          path: 'inventory/query',
          name: 'inventory-query',
          component: () => import('@/views/inventory/InventoryQuery.vue'),
        },
        {
          path: 'inventory/inbound-list', // 调整为更清晰的命名
          name: 'inventory-inbound-list',
          component: () => import('@/views/inventory/InventoryInboundList.vue'),
        },
        {
          path: 'inventory/inbound-post',
          name: 'inventory-inbound-post',
          component: () => import('@/views/inventory/InventoryInboundPost.vue'),
        },
        {
          path: 'inventory/outbound',
          name: 'inventory-outbound',
          component: () => import('@/views/inventory/InventoryOutbound.vue'),
        },
        {
          path: 'inventory/transfer-list',
          name: 'inventory-transfer-list',
          component: () => import('@/views/inventory/InventoryTransferList.vue'),
        },
        {
          path: 'inventory/transfer-post',
          name: 'inventory-transfer-post',
          component: () => import('@/views/inventory/InventoryTransferPost.vue'),
        },
        // 订单管理
        {
          path: 'order/post',
          name: 'order-post',
          component: () => import('@/views/order/OrderPost.vue'),
        },

        // 系统管理
        {
          path: 'system/user',
          name: 'system-user',
          component: () => import('@/views/system/SystemUser.vue'),
        },
        {
          path: 'system/roles',
          name: 'system-roles',
          component: () => import('@/views/system/SystemRoles.vue'),
        },
        {
          path: 'driver/approval',
          name: 'driver-approval',
          component: () => import('@/views/driver/DriverApproval.vue')
        },
        // 选品单管理
        {
          path: 'selection/list',
          name: 'selection-list',
          component: () => import('@/views/selection/SelectionList.vue'),
        },
      ],
    },
  ],
});

export default router;