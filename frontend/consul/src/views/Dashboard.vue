<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import router from '@/router';
import { ChromeFilled, Location, DocumentCopy, Box, Search, Upload, Monitor, Switch, Document, FolderChecked, Van, Service, Setting, User, Lock, Menu } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "@/stores/user";
import instance from '@/utils/axios';
import { logoutService } from '@/api/auth';
// 后端现在有登出接口了

// 获取当前用户信息
const userStore = useUserStore();
const currentUser = userStore.getUserInfo();

if (!currentUser) {
  ElMessage.error('未登录，请先登录');
  router.push('/login');
}

// 控制侧边栏是否折叠
const isCollapse = ref(false);

// 处理菜单点击事件
const handleMenuSelect = (index: string) => {
  router.push(index);
};

// 添加时间相关逻辑
const currentTime = ref(new Date().toLocaleTimeString());
let timer: number | null = null;

// 退出登录方法 - 清理服务器端token，然后清理本地数据
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
      .then(async () => {
        try {
          // 先调用后端登出API清理服务器端token
                  await logoutService();
        } catch (error) {
          console.warn('⚠️ 清理服务器端token失败:', error);
          // 即使后端登出失败，也继续清理前端数据
        }
        
        // 清理用户信息和本地存储
        userStore.clearUserInfo();
        localStorage.clear();
        sessionStorage.clear();
        ElMessage.success('退出登录成功');
        router.push('/login');
      })
      .catch(() => {
        ElMessage.info('已取消退出');
      });
};

onMounted(() => {
  timer = setInterval(() => {
    currentTime.value = new Date().toLocaleTimeString();
  }, 1000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<template>
  <div class="common-layout">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '200px'" class="aside">
        <div class="logo" :class="{ 'logo-collapsed': isCollapse }" @click="router.push('/dashboard/welcome')">
          <el-icon class="logo-icon"><ChromeFilled /></el-icon>
          <span v-show="!isCollapse">陶选</span>
        </div>
        <el-menu
            router
            :default-active="$route.path"
            :collapse="isCollapse"
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
        >
          <!-- 仓库管理 -->
          <el-sub-menu index="1">
            <template #title>
              <el-icon><Location /></el-icon>
              <span>仓库管理</span>
            </template>
            <el-menu-item index="/dashboard/warehouse/list">
              <el-icon><DocumentCopy /></el-icon>
              <template #title>仓库列表</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 库存管理 -->
          <el-sub-menu index="2">
            <template #title>
              <el-icon><Box /></el-icon>
              <span>库存管理</span>
            </template>
            <el-menu-item index="/dashboard/inventory/query">
              <el-icon><Search /></el-icon>
              <template #title>库存查询</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/inventory/inbound-post">
              <el-icon><Upload /></el-icon>
              <template #title>提交入库</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/inventory/inbound-list">
              <el-icon><Monitor /></el-icon>
              <template #title>入库记录</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/inventory/outbound">
              <el-icon><Monitor /></el-icon>
              <template #title>出库记录</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/inventory/transfer-post">
              <el-icon><Upload /></el-icon>
              <template #title>创建调库</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/inventory/transfer-list">
              <el-icon><Monitor /></el-icon>
              <template #title>调库记录</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 订单管理 -->
          <el-sub-menu index="3">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>订单模块</span>
            </template>
            <el-menu-item index="/dashboard/selection/list">
              <el-icon><Service /></el-icon>
              <template #title>选品单管理</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/order/post">
              <el-icon><FolderChecked /></el-icon>
              <template #title>创建订单</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/order/list">
              <el-icon><Van /></el-icon>
              <template #title>订单管理</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/order/delivery">
              <el-icon><Van /></el-icon>
              <template #title>订单派送</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/driver/approval">
              <el-icon><User /></el-icon>
              <template #title>司机审核</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 客户管理 -->
          <el-sub-menu index="6">
            <template #title>
              <el-icon><User /></el-icon>
              <span>客户管理</span>
            </template>
            <el-menu-item index="/dashboard/customer/list">
              <el-icon><User /></el-icon>
              <template #title>客户列表</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 营销管理 -->
          <el-sub-menu index="7">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>营销管理</span>
            </template>
            <el-menu-item index="/dashboard/coupon/list">
              <el-icon><DocumentCopy /></el-icon>
              <template #title>优惠券管理</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/points/list">
              <el-icon><Document /></el-icon>
              <template #title>积分管理</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/member/level">
              <el-icon><User /></el-icon>
              <template #title>会员等级</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 系统管理 -->
          <el-sub-menu index="4">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/dashboard/system/user">
              <el-icon><User /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
            <el-menu-item index="/dashboard/system/roles">
              <el-icon><Lock /></el-icon>
              <template #title>角色权限</template>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 主区域 -->
      <el-container>
        <!-- 头部 -->
        <el-header class="header">
          <div class="header-left">
            <el-icon class="toggle-icon" @click="isCollapse = !isCollapse">
              <Menu />
            </el-icon>
            <span class="header-time">{{ currentTime }}</span>
          </div>
          <div class="header-right">
            <el-dropdown>
              <span class="user-info">
                <el-avatar size="small" :src="userStore.getUserInfo()?.avatar || ''" />
                <span class="username">{{userStore.getUserInfo()?.username || '用户'}}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="router.push('/dashboard/system/user')">个人中心</el-dropdown-item>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 主内容 -->
        <el-main class="main">
          <el-card class="content-card">
            <RouterView />
          </el-card>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
:host {
  display: block;
  margin: 0;
  padding: 0;
  height: 100vh;
  width: 100vw;

}

.common-layout {
  height: 100%;
  width: 100%;

}

.layout-container {
  height: 100%;
  width: 100%;

}

.aside {
  background-color: #545c64;
  transition: width 0.3s;

  border-radius: 18px 0 0 18px;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  background-color: #434a50;
  transition: all 0.3s;
  cursor: pointer;
}

.logo:hover {
  background-color: #373d42;
}

.logo-collapsed {
  font-size: 14px;
}

.logo-icon {
  margin-right: 8px;
  font-size: 24px;
}

.logo-collapsed .logo-icon {
  margin-right: 0;
  font-size: 28px;
}

.header {
  background-color: #545c64;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 20px;

  border-radius: 0 18px 0 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.toggle-icon {
  font-size: 24px;
  cursor: pointer;
  margin-right: 20px;
  color: #e4d9d9;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 8px;
  color: #e4d9d9;
}

.header-time {
  color: #e4d9d9;
}

.main {
  background-color: #cac6c6;
  padding: 20px;
  overflow: auto; /* 保留滚动 */
  height: calc(100vh - 76px);
  border-radius: 0 0 18px;
}

.content-card {
  background-color: #fff;
  border-radius: 18px;
  height: 85vh;
  overflow-y: auto; /* 添加垂直滚动 */
  overflow-x: auto; /* 添加垂直滚动 */
}

.aside {
  border-right: none !important;
  transition: width 0.5s ease-in;
}

.el-menu {
  border-right: none !important;
}

.el-menu--collapse {
  transition-duration: 0.3s;
  box-shadow: none !important;
}

.el-menu-item span,
.el-sub-menu__title span {
  transition: opacity 0.4s ease-in 0.1s;
  opacity: 1;
  visibility: visible;
  display: inline-block;
  white-space: nowrap;
  min-width: 80px;
}

.el-menu--collapse .el-menu-item span,
.el-menu--collapse .el-sub-menu__title span {
  opacity: 0;
  visibility: hidden;
  min-width: 0;
  transition: opacity 0.3s ease-in;
}
</style>