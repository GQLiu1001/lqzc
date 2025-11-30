import axios from '@/utils/axios'; // 主系统的 axios 实例 (8001端口)
// import deliveryInstance from '@/utils/deliveryAxios'; // 暂时注释掉8002端口的实例
import type { 
    ApiResponse, 
    PaginationData, 
    DispatchOrderItem, 
    DispatchOrderQueryParams,
    AvailableOrderItem,
    RobOrderReq,
    RouteResp,
    OperationResp
} from '@/types/interfaces';

// === 腾讯地图集成 ===

// 腾讯地图路线规划 - 改为使用8001端口
export const getRoute = (fromLat: number, toLat: number, fromLng: number, toLng: number): Promise<ApiResponse<RouteResp>> => {
  const params = {
    fromLat,
    toLat,
    fromLng,
    toLng
  };
  return axios.get('/route', { params });
};

// === 司机订单管理 ===

// 获取订单列表 - 改为使用8001端口
export const getDeliveryOrders = (params: DispatchOrderQueryParams): Promise<ApiResponse<PaginationData<DispatchOrderItem>>> => {
  return axios.get('/delivery/list', { params });
};

// 获取可用新订单 - 修复API路径和参数，支持完整的搜索参数
export const getAvailableOrders = (
  status: number = 0, 
  current: number = 1, 
  size: number = 10,
  searchParams?: {
    startTime?: string;
    endTime?: string;
    customerPhone?: string;
  }
): Promise<ApiResponse<any>> => {
  const params: any = {
    current,
    size
  };
  
  // 添加可选的搜索参数
  if (searchParams?.startTime) {
    params.startTime = searchParams.startTime;
  }
  if (searchParams?.endTime) {
    params.endTime = searchParams.endTime;
  }
  if (searchParams?.customerPhone) {
    params.customerPhone = searchParams.customerPhone;
  }
  
  return axios.get(`/orders/fetch/${status}`, { params });
};

// 司机抢单 - 改为使用8001端口
export const robOrder = (id: number, orderNo: string): Promise<ApiResponse<boolean>> => {
  return axios.post(`/delivery/rob/${id}/${orderNo}`);
};

// 完成订单 - 改为使用8001端口
export const completeOrder = (orderNo: string): Promise<ApiResponse<any>> => {
  return axios.post(`/delivery/complete/${orderNo}`);
};

// 取消订单 - 改为使用8001端口
export const cancelOrder = (orderNo: string): Promise<ApiResponse<any>> => {
  return axios.post(`/delivery/cancel/${orderNo}`);
};

// 注意：以下函数在后端文档中不存在，提供占位符实现避免前端报错

// 获取待处理订单 (占位符)
export const getPendingOrders = (params?: any): Promise<ApiResponse<any[]>> => {
    console.warn('getPendingOrders接口不存在，请使用getAvailableOrders');
    // 重定向到现有的接口
    return getAvailableOrders();
};
