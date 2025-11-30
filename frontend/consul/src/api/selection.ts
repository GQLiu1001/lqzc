import axios from "@/utils/axios";
import type { 
  ApiResponse, 
  PaginationData, 
  SelectionListItem,
  SelectionListQueryParams,
  SelectionItemRecord,
  SelectionListChangeReq,
  SelectionItemAddReq
} from "@/types/interfaces";

// 分页查询选品单列表
export const getSelectionLists = (params: SelectionListQueryParams): Promise<ApiResponse<PaginationData<SelectionListItem>>> => {
  return axios.get('/selection/lists', { params });
};

// 查询选品单详情
export const getSelectionListDetail = (id: number): Promise<ApiResponse<SelectionItemRecord[]>> => {
  return axios.get(`/selection/lists/${id}`);
};

// 更新选品单处理状态
export const updateSelectionStatus = (id: number, status: number): Promise<ApiResponse<any>> => {
  return axios.put(`/selection/lists/${id}/status/${status}`);
};

// 删除选品单
export const deleteSelectionList = (id: number): Promise<ApiResponse<any>> => {
  return axios.delete(`/selection/lists/${id}`);
};

// 修改选品单主信息
export const updateSelectionList = (id: number, data: SelectionListChangeReq): Promise<ApiResponse<any>> => {
  return axios.put(`/selection/lists/${id}`, data);
};

// 向选品单中添加新商品
export const addSelectionItem = (id: number, data: SelectionItemAddReq): Promise<ApiResponse<any>> => {
  return axios.post(`/selection/lists/${id}/items`, data);
};

// 修改选品单中某一项商品的数量
export const updateSelectionItemAmount = (listId: number, itemId: number, amount: number): Promise<ApiResponse<any>> => {
  return axios.put(`/selection/lists/${listId}/items/${itemId}`, null, { params: { amount } });
};

// 从选品单中删除某一项商品
export const deleteSelectionItem = (listId: number, itemId: number): Promise<ApiResponse<any>> => {
  return axios.delete(`/selection/lists/${listId}/items/${itemId}`);
};

// 派发订单
export const dispatchSelectionOrder = (selectionListId: number): Promise<ApiResponse<any>> => {
  return axios.post(`/selection/lists/order/${selectionListId}`);
}; 