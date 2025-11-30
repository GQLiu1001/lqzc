import axios from "@/utils/axios";
import type { 
    ApiResponse, 
    PaginationData, 
    LogRecord, 
    LogsQueryParams, 
    LogsChangeReq, 
    LogsInboundReq, 
    LogsTransferReq 
} from "@/types/interfaces";

// 查询出入库及调拨记录
export const getInventoryLogs = (params: LogsQueryParams): Promise<ApiResponse<PaginationData<LogRecord>>> => {
    return axios.get('/logs/list', { params });
};

// 修改出入库或调拨记录
export const updateInventoryLog = (logModel: LogsChangeReq): Promise<ApiResponse<any>> => {
    return axios.put('/logs/change', logModel);
};

// 创建入库记录
export const createInboundLog = (logModel: LogsInboundReq): Promise<ApiResponse<any>> => {
    return axios.post('/logs/inbound', logModel);
};

// 创建调拨记录
export const createTransferLog = (logModel: LogsTransferReq): Promise<ApiResponse<any>> => {
    return axios.post('/logs/transfer', logModel);
};

// 删除日志记录
export const deleteInventoryLog = (id: number): Promise<ApiResponse<any>> => {
    return axios.delete(`/logs/delete/${id}`);
};

// 向后兼容的函数名
export const postInboundLog = createInboundLog;
export const postTransferLog = createTransferLog;