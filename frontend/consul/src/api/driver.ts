import axios from '@/utils/axios';
import type { ApiResponse, DriverListData, Driver, DriverLoginReq, DriverLoginResp, DriverLocationUpdateReq } from '@/types/interfaces';

// 获取司机列表 - 管理端（使用端口8001）
export const getAllDrivers = (params?: any): Promise<ApiResponse<DriverListData>> => {
  return axios.get('/manager/driver-list', { params });
};

// 获取司机详情
export const getDriverDetail = (driverId: number) => {
  return axios.get(`/api/delivery/driver/${driverId}`);
};

// 审核司机资格 - 同意
export const approveDriver = (driverId: number, approvalData?: any): Promise<ApiResponse<any>> => {
  return axios.put(`/manager/driver-approval/${driverId}`, approvalData);
};

// 审核司机资格 - 拒绝
export const rejectDriver = (driverId: number, approvalData?: any): Promise<ApiResponse<any>> => {
  return axios.put(`/manager/driver-rejection/${driverId}`, approvalData);
};

// 删除司机
export const deleteDriver = (driverId: number, auditor?: string): Promise<ApiResponse<any>> => {
  return axios.delete(`/manager/driver-delete/${driverId}`, {
    data: { auditor }
  });
};

// 清零司机钱包
export const resetDriverMoney = (driverId: number, auditor?: string): Promise<ApiResponse<any>> => {
  return axios.delete(`/manager/driver-reset-money/${driverId}`, {
    data: { auditor }
  });
};

// === 以下是配送端的司机接口（使用端口8002） ===

// 司机登录 - 修复参数传递方式
export const driverLogin = (loginData: DriverLoginReq): Promise<ApiResponse<DriverLoginResp>> => {
  const params = new URLSearchParams();
  params.append('code', loginData.code);
  params.append('phone', loginData.phone);
  
  return axios.post('/driver/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
};

// 获取司机审核状态
export const getDriverAuditStatus = (id: number): Promise<ApiResponse<number>> => {
  return axios.get(`/driver/audit-status/${id}`);
};

// 司机登出
export const driverLogout = (id: number): Promise<ApiResponse<any>> => {
  return axios.post(`/driver/logout/${id}`);
};

// 更新司机状态
export const changeDriverStatus = (id: number, status: number): Promise<ApiResponse<any>> => {
  return axios.post(`/driver/info/change-status/${id}/${status}`);
};

// 获取钱包信息
export const getDriverWallet = (id: number): Promise<ApiResponse<number>> => {
  return axios.get(`/driver/info/wallet/${id}`);
};

// 更新司机经纬度地址
export const updateDriverLocation = (locationData: DriverLocationUpdateReq): Promise<ApiResponse<any>> => {
  const params = new URLSearchParams();
  params.append('id', locationData.id.toString());
  params.append('latitude', locationData.latitude.toString());
  params.append('longitude', locationData.longitude.toString());
  
  return axios.post('/driver/info/update-location', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
};