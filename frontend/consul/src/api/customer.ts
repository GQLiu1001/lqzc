import axios from "@/utils/axios";
import type { ApiResponse } from "@/types/interfaces";

// 客户信息接口
export interface Customer {
    id: number;
    nickname: string;
    phone: string;
    avatar?: string;
    level?: number;
    level_name?: string;
    status?: number;
    create_time?: string;
}

// 客户地址接口
export interface CustomerAddress {
    id: number;
    customer_id?: number;
    receiver_name: string;
    receiver_phone: string;
    province: string;
    city: string;
    district: string;
    detail: string;
    tag?: string;
    is_default?: number;
    latitude?: number;
    longitude?: number;
}

// 查询客户列表
export const getCustomerList = (params: any): Promise<ApiResponse<any>> => {
    return axios.get('/customer/list', { params });
};

// 获取客户详情
export const getCustomerDetail = (id: number): Promise<ApiResponse<any>> => {
    return axios.get(`/customer/detail/${id}`);
};

// 获取客户地址列表 (Admin API)
// 支持通过手机号或客户ID获取地址
export const getCustomerAddresses = (phone: string): Promise<ApiResponse<CustomerAddress[]>> => {
    return axios.get('/admin/customer/address/list', { params: { phone } });
};

// 通过客户ID获取地址列表
export const getCustomerAddressesById = (customerId: number): Promise<ApiResponse<CustomerAddress[]>> => {
    return axios.get('/admin/customer/address/list', { params: { customer_id: customerId } });
};

// 为客户添加地址 (Admin API)
export const addCustomerAddress = (data: CustomerAddress): Promise<ApiResponse<any>> => {
    return axios.post('/admin/customer/address/add', data);
};

// 更新客户地址 (Admin API)
export const updateCustomerAddress = (data: CustomerAddress): Promise<ApiResponse<any>> => {
    return axios.put('/admin/customer/address/update', data);
};

// 删除客户地址 (Admin API)
export const deleteCustomerAddress = (id: number): Promise<ApiResponse<any>> => {
    return axios.delete(`/admin/customer/address/delete/${id}`);
};

// ========== Admin Customer Management APIs ==========

// 客户详情响应接口
export interface CustomerDetailResponse {
    base_info: {
        id: number;
        nickname: string;
        phone: string;
        avatar?: string;
        level: number;
        level_name: string;
        status: number;
        register_channel?: string;
        create_time: string;
    };
    assets: {
        points_balance: number;
        coupon_count: number;
    };
    stats: {
        total_orders: number;
        total_spent: number;
    };
}

// 客户列表查询参数
export interface CustomerListParams {
    current?: number;
    size?: number;
    keyword?: string;
    level?: number;
    status?: number;
}

// 创建客户请求
export interface CreateCustomerRequest {
    phone: string;
    nickname: string;
    password?: string;
    gender?: number;
    remark?: string;
}

// 更新客户状态请求
export interface UpdateCustomerStatusRequest {
    status: number;
    reason?: string;
}

// Admin: 客户列表查询
export const getAdminCustomerList = (params: CustomerListParams): Promise<ApiResponse<any>> => {
    return axios.get('/admin/customer/list', { params });
};

// Admin: 创建客户
export const createCustomer = (data: CreateCustomerRequest): Promise<ApiResponse<any>> => {
    return axios.post('/admin/customer/create', data);
};

// Admin: 客户详情
export const getAdminCustomerDetail = (id: number): Promise<ApiResponse<CustomerDetailResponse>> => {
    return axios.get(`/admin/customer/detail/${id}`);
};

// Admin: 更改客户状态
export const updateCustomerStatus = (id: number, data: UpdateCustomerStatusRequest): Promise<ApiResponse<any>> => {
    return axios.put(`/admin/customer/status/${id}`, data);
};
