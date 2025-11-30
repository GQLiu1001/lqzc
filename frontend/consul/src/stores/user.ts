import { defineStore } from "pinia";
import { ref } from "vue";
import type { UserLoginResp } from "@/types/interfaces";

export const useUserStore = defineStore('user', () => {
    // 改进初始化逻辑，增加错误处理
    const userInfo = ref<UserLoginResp | null>(null);

    // 初始化时加载用户信息
    const initUserInfo = () => {
        try {
            const storedUserInfo = localStorage.getItem('userInfo');
            if (storedUserInfo) {
                userInfo.value = JSON.parse(storedUserInfo);
            }
        } catch (error) {
            console.error('解析 localStorage 中的用户信息失败:', error);
            localStorage.removeItem('userInfo'); // 删除无效数据
        }
    };

    // 立即执行初始化
    initUserInfo();

    const setUserInfo = (info: UserLoginResp) => {
        userInfo.value = info;
        localStorage.setItem('userInfo', JSON.stringify(info));
    };

    const getUserInfo = () => {
        // 如果内存中没有，再次尝试从 localStorage 获取
        if (!userInfo.value) {
            try {
                const storedUserInfo = localStorage.getItem('userInfo');
                if (storedUserInfo) {
                    userInfo.value = JSON.parse(storedUserInfo);
                }
            } catch (error) {
                console.error('二次获取用户信息失败:', error);
                localStorage.removeItem('userInfo'); // 删除无效数据
            }
        }
        return userInfo.value;
    };

    const clearUserInfo = () => {
        userInfo.value = null;
        localStorage.removeItem('userInfo');
    };

    // 改进：判断用户是否是管理员的便捷方法
    const isAdmin = () => {
        const user = getUserInfo(); // 使用 getUserInfo 确保数据是最新的
        return user?.role_id === 1; // 假设role_id为1是管理员
    };

    // 获取token的方法
    const getToken = () => {
        return localStorage.getItem('satoken') || '';
    };

    // 设置token的方法
    const setToken = (token: string) => {
        localStorage.setItem('satoken', token);
    };

    // 登出方法，清除用户信息和token
    const logout = () => {
        clearUserInfo();
        localStorage.removeItem('satoken');
    };

    return {
        userInfo,
        setUserInfo,
        getUserInfo,
        clearUserInfo,
        isAdmin,
        getToken,
        setToken,
        logout,
    };
});