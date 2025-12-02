// api/order.ts
import axios from "@/utils/axios";
import type {
    ApiResponse,
    PaginationData,
    OrderNewReq,
    OrderListItem,
    OrderQueryParams,
    OrderDetailResp,
    OrderChangeReq,
    OrderSubChangeReq,
    OrderDispatchReq
} from "@/types/interfaces";

// order.ts
// 创建新订单
export const postOrder = (orderModel: OrderNewReq): Promise<ApiResponse<any>> => {
    return axios.post('/orders/new', orderModel);
};

// 查询订单列表
export const getOrders = (params: OrderQueryParams): Promise<any> => {
    return axios.get('/orders/list', { params });
};

// 查询订单详情
export const getOrderDetail = (id: number): Promise<any> => {
    return axios.get(`/orders/detail/${id}`);
};

// 修改订单信息
export const updateOrder = (orderModel: OrderChangeReq): Promise<ApiResponse<any>> => {
    return axios.put('/orders/change', orderModel);
};

// 修改指定子订单项信息
export const updateOrderItem = (itemModel: OrderSubChangeReq): Promise<ApiResponse<any>> => {
    return axios.put('/orders/change-sub', itemModel);
};

// 删除订单
export const deleteOrder = (orderId: number): Promise<ApiResponse<any>> => {
    return axios.delete(`/orders/delete/${orderId}`);
};

// 更改订单派送状态（并确认支付和使用优惠券）
export const updateDispatchStatus = (id: number, status: number, payMethod?: string, couponId?: number): Promise<ApiResponse<any>> => {
    const params: any = {};
    if (payMethod) {
        params.pay_method = payMethod;
    }
    if (couponId) {
        params.coupon_id = couponId;
    }
    return axios.put(`/orders/change/dispatch-status/${id}/${status}`, null, { params });
};

// 获取用户可用优惠券
export interface AvailableCoupon {
    coupon_id: number;
    title: string;
    type: number;
    threshold_amount: number | null;
    discount_amount: number | null;
    discount_rate: number | null;
    max_discount: number | null;
    expire_time: string;
    calculated_discount: number | null;
    usable: boolean;
}

export const getAvailableCoupons = (customerPhone: string, orderAmount?: number): Promise<ApiResponse<AvailableCoupon[]>> => {
    const params: any = { customerPhone };
    if (orderAmount !== undefined) {
        params.orderAmount = orderAmount;
    }
    return axios.get('/admin/coupon/available', { params });
};

// 后台确认收货（同时发放积分）
export const confirmReceive = (orderId: number): Promise<ApiResponse<any>> => {
    return axios.post(`/orders/confirm-receive/${orderId}`);
};

// 派送订单
export const dispatchOrder = (orderModel: OrderDispatchReq): Promise<ApiResponse<any>> => {
    return axios.post('/orders/dispatch', orderModel);
};

// 注意：以下函数在后端文档中不存在，提供占位符实现避免前端报错
// 实际应用中应该使用正确的子订单管理接口

// 添加订单项
export const addOrderItem = (orderId: number, itemModel: any): Promise<ApiResponse<any>> => {
    const requestData = { ...itemModel, order_id: orderId, change_type: 1 };
    return axios.put('/orders/change-sub', requestData);
};

// 删除订单项
export const deleteOrderItem = (itemId: number): Promise<ApiResponse<any>> => {
    const requestData = { id: itemId, change_type: 2 };
    return axios.put('/orders/change-sub', requestData);
};
