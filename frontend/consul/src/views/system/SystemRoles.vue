<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getUsers, deleteUser } from '@/api/user';
import type { UserListItem, PaginationParams } from '@/types/interfaces';
import { useUserStore } from '@/stores/user';

// Store user list and pagination state
const userList = ref<UserListItem[]>([]);
const page = ref(1);
const size = ref(10);
const total = ref(0);

// 获取当前用户信息
const userStore = useUserStore();
const currentUser = ref(userStore.getUserInfo());

// 使用计算属性来判断是否有删除权限
const hasDeletePermission = computed(() => {
  const user = userStore.getUserInfo();
  console.log('权限检查 - 当前用户:', user);
  return user?.role_id === 1; // role_id为1表示管理员
});

// Fetch user list with pagination
const fetchUserList = async () => {
  try {
    const params: PaginationParams = {
      current: page.value,
      size: size.value,
    };

    const result = await getUsers(params);
    if (result.data.code === 200 && result.data.data?.records) {
      userList.value = result.data.data.records;
      total.value = result.data.data.total || 0;
    } else {
      throw new Error('数据格式异常');
    }
  } catch (error) {
    console.error('Failed to fetch user list:', error);
    ElMessage.error('获取用户列表失败，请稍后重试');
  }
};

// 删除用户
const handleDelete = async (userId: number, username: string) => {
  if (!hasDeletePermission.value) {
    ElMessage.error('无权限执行删除操作');
    return;
  }

  try {
    await ElMessageBox.confirm(
        `确定要删除用户 "${username}" 吗？此操作不可恢复！`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
    );

    const response = await deleteUser(userId);
    if (response.data.code === 200) {
      ElMessage.success('删除成功');
      await fetchUserList();
    } else {
      throw new Error(response.data.message || '删除失败');
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete user:', error);
      ElMessage.error(error.message || '删除用户失败，请稍后重试');
    }
  }
};

// Pagination handlers
const handlePageChange = (newPage: number) => {
  page.value = newPage;
  fetchUserList();
};

const handleSizeChange = (newSize: number) => {
  size.value = newSize;
  page.value = 1;
  fetchUserList();
};

onMounted(() => {
  // 首先检查用户信息
  currentUser.value = userStore.getUserInfo();
  console.log('组件挂载 - 当前用户信息:', currentUser.value);

  // 如果没有用户信息，可以在这里添加重新获取用户信息的逻辑
  // 例如：重定向到登录页、刷新用户信息等

  // 然后获取用户列表
  fetchUserList();
});
</script>

<template>
  <div class="page-container">
    <h1>用户管理</h1>
    <hr>

    <!-- 显示当前用户信息（调试用） -->
    <div v-if="false" class="debug-info">
      <p>当前用户: {{ currentUser?.username }}</p>
      <p>角色ID: {{ currentUser?.role_id }}</p>
      <p>是否有删除权限: {{ hasDeletePermission }}</p>
    </div>

    <!-- 用户列表 -->
    <div class="user-list-container">
      <h2>所有用户</h2>
      <el-table :data="userList" style="width: 100%">
        <el-table-column prop="id" label="用户id" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="phone" label="手机号" />
        <!-- 使用计算属性控制整列显示 -->
        <el-table-column label="操作" v-if="hasDeletePermission">
          <template #default="{ row }">
            <el-button
                type="danger"
                size="small"
                @click="handleDelete(row.id, row.username)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
            :current-page="page"
            :page-size="size"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>


<style scoped>
.page-container {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.user-list-container {
  width: 100%;
  align-content: center;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow-y: auto;
  overflow-x: auto;
}

h1 {
  margin-bottom: 20px;
}

h2 {
  margin-bottom: 15px;
}

hr {
  width: 100%;
  max-width: 700px;
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-bottom: 20px;
}

/* Ensure table columns are evenly spaced */
.el-table th, .el-table td {
  text-align: center; /* Center-align text for better appearance */
}

.el-table .el-table__cell {
  padding: 10px; /* Adjust padding for consistency */
  height: 100%;
}
</style>