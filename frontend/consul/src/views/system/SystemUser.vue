<template>
  <div class="page-container">
    <h1>用户管理</h1>
    <hr />
    <el-form :model="userForm" label-width="100px" class="user-form">
      <el-form-item label="用户名" required>
        <el-input v-model="userForm.username" placeholder="请输入用户名" />
      </el-form-item>

      <el-form-item label="电话" required>
        <el-input v-model="userForm.phone" placeholder="请输入电话" maxlength="11" />
      </el-form-item>

      <el-form-item label="旧密码">
        <el-input
            v-model="userForm.oldPassword"
            type="password"
            placeholder="请输入旧密码（修改密码时必填）"
            show-password
        />
      </el-form-item>

      <el-form-item label="新密码">
        <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入新密码（可选）"
            show-password
        />
      </el-form-item>

      <el-form-item label="确认密码">
        <el-input
            v-model="userForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码（可选）"
            show-password
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitUserInfo">提交</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/user';
import { updateUser } from '@/api/user';
import router from '@/router';

// 获取当前用户信息
const userStore = useUserStore();
const currentUser = userStore.getUserInfo();

if (!currentUser) {
  ElMessage.error('未登录，请先登录');
  router.push('/login');
}

// 用户表单数据 - 修改字段名与API一致
const userForm = ref({
  username: currentUser?.username || '',
  phone: currentUser?.phone || '',
  oldPassword: '',  // 旧密码
  password: '',     // 新密码 - 字段名改为与API匹配
  confirmPassword: '', // 确认密码 (前端验证用)
});

// 用户 ID
const userId = ref<number>(currentUser?.id || 0);

// 提交用户信息
const submitUserInfo = async () => {
  try {
    if (!userForm.value.username) {
      ElMessage.error('用户名是必填项');
      return;
    }

    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!userForm.value.phone || !phoneRegex.test(userForm.value.phone)) {
      ElMessage.error('请输入有效的11位手机号码');
      return;
    }

    // 密码相关校验
    if (userForm.value.oldPassword || userForm.value.password || userForm.value.confirmPassword) {
      if (!userForm.value.oldPassword) {
        ElMessage.error('请输入旧密码');
        return;
      }
      if (!userForm.value.password) {
        ElMessage.error('请输入新密码');
        return;
      }
      if (!userForm.value.confirmPassword) {
        ElMessage.error('请再次输入新密码');
        return;
      }
      if (userForm.value.password !== userForm.value.confirmPassword) {
        ElMessage.error('两次输入的新密码不一致');
        return;
      }
      if (userForm.value.password.length < 6) {
        ElMessage.error('新密码长度需至少6位');
        return;
      }
    }

    // 构建提交数据 - 按API文档格式
    const submitData: {
      username: string;
      phone: string;
      password?: string;
      new_password?: string;
    } = {
      username: userForm.value.username,
      phone: userForm.value.phone,
    };

    // 如果用户修改了密码，添加密码字段
    if (userForm.value.password) {
      submitData.password = userForm.value.oldPassword; // 旧密码
      submitData.new_password = userForm.value.password; // 新密码
    }

    // 调用 updateUser 更新用户信息
    const response = await updateUser(submitData);

    if (response.data.code === 200) {
      // 更新本地存储的用户信息
      const updatedUserInfo = {
        ...currentUser!,
        username: userForm.value.username,
        phone: userForm.value.phone,
        avatar: currentUser?.avatar || '',
      };
      userStore.setUserInfo(updatedUserInfo);

      ElMessage.success('用户信息更新成功');

      // 如果更新了密码，清空密码字段
      if (userForm.value.password) {
        userForm.value.oldPassword = '';
        userForm.value.password = '';
        userForm.value.confirmPassword = '';
      }
    } else {
      throw new Error(response.data.message || '更新失败');
    }
  } catch (error: any) {
    console.error('更新用户信息失败:', error);
    ElMessage.error(`更新失败: ${error.message || '请稍后重试'}`);
  }
};

// 重置表单
const resetForm = () => {
  userForm.value = {
    username: currentUser?.username || '',
    phone: currentUser?.phone || '',
    oldPassword: '',
    password: '',
    confirmPassword: '',
  };
};
</script>

<style scoped>
/* 样式保持不变 */
.page-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  max-width: 500px;
  margin: 0 auto;
}

.user-form {
  margin-top: 20px;
  width: 100%;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}

hr {
  width: 100%;
  max-width: 500px;
  margin-bottom: 20px;
}
</style>