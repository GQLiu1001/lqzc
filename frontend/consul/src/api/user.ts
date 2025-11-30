import axios from "@/utils/axios";
import type { ApiResponse, PaginationData, PaginationParams, UserListItem, UserChangeInfoReq } from "@/types/interfaces";

// user.ts
// 获取用户列表 - 使用查询参数
export const getUsers = (params: PaginationParams): Promise<any> => {
    return axios.get('/user/list', { params });
};

// 修改用户信息 - 使用JSON body（PUT请求通常使用JSON）
export const updateUser = (userModel: UserChangeInfoReq): Promise<ApiResponse<any>> => {
    return axios.put('/user/change-info', userModel);
};

// 删除用户 - 路径参数
export const deleteUser = (id: number): Promise<ApiResponse<any>> => {
    return axios.delete(`/user/delete/${id}`);
};

// 注意：后端文档中没有提供头像上传接口，如需要请联系后端添加

