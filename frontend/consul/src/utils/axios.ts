// axios.ts
import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { ElMessage } from 'element-plus';
import router from '@/router';

// 根据环境获取基础URL - 本地测试环境使用代理避免跨域
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

// 创建Axios实例
const instance = axios.create({
    baseURL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
    withCredentials: true,
});

// Axios 请求拦截器
instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // 从 localStorage 获取存储的 token
        let token = localStorage.getItem('satoken');
        
        // 如果存在 token，则添加到请求头，使用 Authorization Bearer 格式
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// 响应拦截器
instance.interceptors.response.use(
    (response: AxiosResponse) => {
        const { data, status } = response;
        
        // 现在token在登录响应的body中，不在header中
        // token的保存逻辑已经移到Login.vue中处理

        if (status === 200) {
            // 特殊处理：上传图片接口直接返回 {url: "..."} 格式
            if (response.config.url?.includes('/upload/image') && data.url) {
                return response;
            }
            // 检查业务状态码
            if (data.code === 200) {
                return response;
            } else {
                // 处理业务错误
                switch (data.code) {
                    case 400:
                        ElMessage.error(data.message || '请求参数错误');
                        break;
                    case 401:
                        ElMessage.error(data.message || '未登录，请重新登录');
                        localStorage.removeItem('satoken');
                        router.push('/login');
                        break;
                    case 403:
                        ElMessage.error(data.message || '未授权，权限不足');
                        break;
                    case 404:
                        ElMessage.error(data.message || '资源未找到');
                        break;
                    case 500:
                        ElMessage.error(data.message || '服务器内部错误');
                        break;
                    default:
                        ElMessage.error(data.message || '未知错误');
                }
                return Promise.reject(new Error(data.message || '请求失败'));
            }
        }
        return response;
    },
    (error) => {
        const { response } = error;
        
        if (response) {
            switch (response.status) {
                case 400:
                    ElMessage.error('请求参数错误');
                    break;
                case 401:
                    ElMessage.error('未登录，请重新登录');
                    localStorage.removeItem('satoken');
                    router.push('/login');
                    break;
                case 403:
                    ElMessage.error('未授权，权限不足');
                    break;
                case 404:
                    ElMessage.error('资源未找到');
                    break;
                case 500:
                    ElMessage.error('服务器内部错误');
                    break;
                default:
                    ElMessage.error(`错误: ${response.status}`);
            }
        } else {
            ElMessage.error('网络异常，请检查后端服务是否启动');
        }
        return Promise.reject(error);
    }
);

export default instance;