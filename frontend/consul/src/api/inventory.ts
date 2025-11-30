import axios from "@/utils/axios";
import type { ApiResponse, PaginationData, InventoryItem, InventoryQueryParams, ItemsChangeReq, ItemsFetchResp } from "@/types/interfaces";

// inventory.ts
// 查询库存列表
export const getInventoryItems = (params: InventoryQueryParams): Promise<ApiResponse<PaginationData<InventoryItem>>> => {
    return axios.get('/inventory/items-list', { params });
};

// 修改库存物品
export const updateInventoryItem = (inventoryModel: ItemsChangeReq): Promise<ApiResponse<any>> => {
    return axios.put('/inventory/items-change', inventoryModel);
};

// 删除库存物品
export const deleteInventoryItem = (id: number): Promise<ApiResponse<any>> => {
    return axios.delete(`/inventory/items-delete/${id}`);
};

// 根据产品型号查询库存信息
export const getInventoryByModelNumber = (model: string): Promise<any> => {
    return axios.get(`/inventory/fetch/${model}`);
};