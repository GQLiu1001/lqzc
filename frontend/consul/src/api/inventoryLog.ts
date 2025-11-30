// inventoryLog.ts
import axios from "@/utils/axios";
import type { 
    ApiResponse, 
    PaginationData, 
    LogRecord, 
    LogsQueryParams, 
    LogsChangeReq, 
    LogsInboundReq, 
    LogsTransferReq,
    LogQueryParams,
    InventoryLogChangeRequest
} from "@/types/interfaces";

// 查询出入库及调拨记录（新版本，用于标准接口）
export const getInventoryLogs = (params: LogsQueryParams): Promise<ApiResponse<PaginationData<LogRecord>>> => {
    return axios.get('/logs/list', { params });
};

// 查询出入库及调拨记录（兼容版本，用于已有页面）
export const getInventoryLogsCompat = async (params: LogQueryParams): Promise<any> => {
    // 将前端参数映射为后端参数
    const backendParams: any = {
        current: params.current || 1,
        size: params.size || 10,
        logType: params.operation_type, // operation_type -> logType
        startTime: params.start_time,   // start_time -> startTime  
        endTime: params.end_time        // end_time -> endTime
    };
    
    try {
        const response = await axios.get('/logs/list', { params: backendParams });
        
        // 如果响应成功且有数据，则映射字段名
        if (response.data.code === 200 && response.data.data?.records) {
            const mappedRecords = response.data.data.records.map((record: any) => ({
                id: record.id,
                inventory_item_id: record.item_id,           // item_id -> inventory_item_id
                operation_type: record.log_type,             // log_type -> operation_type
                quantity_change: record.amount_change,       // amount_change -> quantity_change
                operator_id: record.operator_id,
                source_warehouse: record.source_warehouse,
                target_warehouse: record.target_warehouse,
                remark: record.remark,
                create_time: record.create_time,
                update_time: record.update_time
            }));
            
            // 返回映射后的数据
            return {
                ...response,
                data: {
                    ...response.data,
                    data: {
                        ...response.data.data,
                        records: mappedRecords
                    }
                }
            };
        }
        
        return response;
    } catch (error) {
        throw error;
    }
};

// 修改出入库或调拨记录（标准版本）
export const updateInventoryLog = (logModel: LogsChangeReq): Promise<ApiResponse<any>> => {
    return axios.put('/logs/change', logModel);
};

// 修改出入库或调拨记录（兼容版本）
export const updateInventoryLogCompat = (logModel: InventoryLogChangeRequest, changeType: number): Promise<any> => {
    // 将前端数据映射为后端数据，包含changeType
    const backendData: any = {
        id: logModel.id,
        item_id: logModel.inventory_item_id,      // inventory_item_id -> item_id
        log_type: logModel.operation_type,        // operation_type -> log_type
        amount_change: logModel.quantity_change,  // quantity_change -> amount_change
        source_warehouse: logModel.source_warehouse,
        target_warehouse: logModel.target_warehouse,
        remark: logModel.remark,
        changeType: changeType                    // 将changeType放到请求体中
    };
    
    return axios.put('/logs/change', backendData);
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
export const postTransferLog = createTransferLog;