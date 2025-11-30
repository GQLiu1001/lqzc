import axios from "@/utils/axios";
import type { ApiResponse, LoginRequest, RegisterRequest, ResetPasswordRequest, UserLoginResp } from "@/types/interfaces";

// auth.ts
// 用户登录相关服务
export const loginService = (loginData: LoginRequest): Promise<ApiResponse<UserLoginResp>> => {
    const params = new URLSearchParams();
    params.append('username', loginData.username);
    params.append('password', loginData.password);
    
    return axios.post('/user/login', params, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
};

// 用户注册
export const registerService = (registerData: RegisterRequest): Promise<ApiResponse<any>> => {
    const params = new URLSearchParams();
    params.append('username', registerData.username);
    params.append('password', registerData.password);
    params.append('phone', registerData.phone);
    
    return axios.post('/user/register', params, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
};

// 重置密码
export const resetPasswordService = (resetData: ResetPasswordRequest): Promise<ApiResponse<any>> => {
    const params = new URLSearchParams();
    params.append('username', resetData.username);
    params.append('phone', resetData.phone);
    params.append('new_password', resetData.new_password);
    
    return axios.post('/user/reset', params, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
};

// 用户登出
export const logoutService = (): Promise<ApiResponse<any>> => {
    return axios.get('/user/logout');
};

// 注意：后端登录和登出接口已实现