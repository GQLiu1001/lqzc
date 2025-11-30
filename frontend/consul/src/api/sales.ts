import axios from "@/utils/axios";
import type { ApiResponse, SalesItem, SalesTrendResp } from "@/types/interfaces";
// sales.ts
// 获取销量前五商品
export const getTopProducts = (): Promise<any> => {
    return axios.get('/sales/top-products');
};

// 获取销售趋势报表
export const getSalesTrend = (year: number, month: number, length: number): Promise<any> => {
    return axios.get(`/sales/trend/${year}/${month}/${length}`);
};

// 向后兼容的函数名
export const fetchTopProducts = getTopProducts;
export const fetchSalesTrend = getSalesTrend;

// 注意：以下接口在后端文档中不存在，提供占位符实现避免前端报错
// 实际应用中应该移除这些调用或联系后端添加相应接口

// 获取今日销售金额 (占位符实现)
export const fetchTodaySalesAmount = (): Promise<ApiResponse<any>> => {
    // 返回模拟数据，避免前端报错
    return Promise.resolve({
        code: 200,
        message: 'success',
        data: {
            today_sale_amount: 0
        }
    });
};

// 获取总销售金额 (占位符实现)
export const fetchTotalSalesAmount = (): Promise<ApiResponse<any>> => {
    // 返回模拟数据，避免前端报错
    return Promise.resolve({
        code: 200,
        message: 'success',
        data: {
            total_sale_amount: 0
        }
    });
};