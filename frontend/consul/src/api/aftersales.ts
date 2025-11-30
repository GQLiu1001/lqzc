// api/aftersales.ts
import axios from "@/utils/axios";
import type { ApiResponse } from "@/types/interfaces";

// 注意：以下函数在后端文档中不存在，提供占位符实现避免前端报错
// 实际应用中应该联系后端添加相应的售后接口

// 创建售后申请 (占位符)
export const createAftersale = (data: any): Promise<ApiResponse<any>> => {
    console.warn('createAftersale接口不存在，请联系后端添加');
    return Promise.reject(new Error('售后接口不存在'));
};

// 获取订单售后记录 (占位符)
export const getOrderAftersaleLogs = (orderId: number): Promise<ApiResponse<any[]>> => {
    console.warn('getOrderAftersaleLogs接口不存在，请联系后端添加');
    return Promise.resolve({
        code: 200,
        message: 'success',
        data: []
    });
};

// 更新售后状态 (占位符)
export const updateAftersaleStatus = (id: number, status: number): Promise<ApiResponse<any>> => {
    console.warn('updateAftersaleStatus接口不存在，请联系后端添加');
    return Promise.reject(new Error('售后接口不存在'));
};
// 目前接口文档中没有提供售后相关的接口

export const placeholder = (): Promise<ApiResponse<any>> => {
    return axios.get('/placeholder');
};