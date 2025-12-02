// 生产环境API地址 - 使用nginx代理路径
const API_BASE_URL = '/api';

// C端用户token的localStorage键名
const CUSTOMER_TOKEN_KEY = 'mall_customer_token';

// ==================== Token管理 ====================

// 获取C端用户token
export const getCustomerToken = (): string | null => {
  return localStorage.getItem(CUSTOMER_TOKEN_KEY);
};

// 设置C端用户token
export const setCustomerToken = (token: string) => {
  localStorage.setItem(CUSTOMER_TOKEN_KEY, token);
};

// 清除C端用户token
export const clearCustomerToken = () => {
  localStorage.removeItem(CUSTOMER_TOKEN_KEY);
};

// 检查是否已登录
export const isLoggedIn = (): boolean => {
  return !!getCustomerToken();
};

// ==================== 请求方法 ====================

// 无需登录的fetch请求（商品列表等）
const publicFetch = async (url: string, options: RequestInit = {}) => {
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
};

// 需要登录的fetch请求（购物车、个人中心等）
const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
  const token = getCustomerToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['X-Customer-Token'] = token;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // 如果401，清除本地token
  if (response.status === 401) {
    clearCustomerToken();
  }

  return response;
};

// ==================== 类型定义 ====================

export interface Product {
  model: string;
  manufacturer: string;
  specification: string;
  surface: number;
  category: number;
  total_amount: number;
  selling_price: number;
  picture: string;
  remark?: string;
}

export interface ProductListParams {
  current?: number;
  size?: number;
  category?: string;
  surface?: string;
}

export interface ProductListResponse {
  total: number;
  current: number;
  size: number;
  records: Product[];
}

export interface CartItem {
  model: string;
  amount: number;
  subtotal_price: number;
  selling_price: number;
}

export interface CartChangeRequest {
  model: string;
  amount: number;
}

export interface CartDeleteRequest {
  model: string;
}

export interface OrderItem {
  model: string;
  amount: number;
}

export interface OrderRequest {
  customer_phone: string;
  total_price: number;
  items: OrderItem[];
  remark?: string;
  delivery_address: string;
}

export interface UserProfile {
  id: number;
  nickname: string;
  phone: string;
  avatar: string;
  email?: string;
  gender?: number;
  level?: number;
  level_name?: string;
  points_balance?: number;
  coupon_count?: number;
}

export interface LoginRequest {
  phone: string;
  password: string;
}

export interface RegisterRequest {
  phone: string;
  nickname?: string;
  password: string;
  register_channel?: string;
}

export interface ResetPasswordRequest {
  phone: string;
  old_password: string;
  new_password: string;
}

export interface ForgotPasswordRequest {
  phone: string;
  sms_code: string;
  new_password: string;
}

export interface LoginResponse {
  token: string;
  customer: {
    id: number;
    nickname: string;
    phone: string;
    avatar: string;
    level: number;
    level_name: string;
  };
}

// ==================== 映射表 ====================

export const surfaceMap: { [key: number]: string } = {
  1: '抛光',
  2: '哑光',
  3: '釉面',
  4: '通体大理石',
  5: '微晶石',
  6: '岩板'
};

export const categoryMap: { [key: number]: string } = {
  1: '墙砖',
  2: '地砖',
  3: '胶',
  4: '洁具'
};

export const surfaceReverseMap: { [key: string]: number } = {
  '抛光': 1,
  '哑光': 2,
  '釉面': 3,
  '通体大理石': 4,
  '微晶石': 5,
  '岩板': 6
};

export const categoryReverseMap: { [key: string]: number } = {
  '墙砖': 1,
  '地砖': 2,
  '胶': 3,
  '洁具': 4
};

// ==================== 商品API（无需登录） ====================

export const mallApi = {
  // 获取商品列表（无需登录）
  getProductList: async (params: ProductListParams = {}): Promise<ProductListResponse> => {
    const queryParams = new URLSearchParams();

    if (params.current) queryParams.append('current', params.current.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.category && params.category !== '全部') {
      const categoryNum = categoryReverseMap[params.category];
      if (categoryNum) queryParams.append('category', categoryNum.toString());
    }
    if (params.surface && params.surface !== '全部') {
      const surfaceNum = surfaceReverseMap[params.surface];
      if (surfaceNum) queryParams.append('surface', surfaceNum.toString());
    }

    const response = await publicFetch(
      `${API_BASE_URL}/mall/items/list?${queryParams.toString()}`
    );

    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取商品列表失败');
    }
  },
};

// ==================== 购物车API（需要登录） ====================

export const cartApi = {
  // 查看购物车
  getCart: async (): Promise<CartItem[]> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/cart`);
    const result = await response.json();

    if (result.code === 200) {
      if (result.data === null || result.data === undefined) {
        return [];
      }
      if (Array.isArray(result.data)) {
        return result.data;
      }
      return [];
    } else {
      throw new Error(result.message || '获取购物车失败');
    }
  },

  // 添加到购物车
  addToCart: async (request: CartChangeRequest): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/cart/add`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '添加到购物车失败');
    }
  },

  // 修改购物车
  changeCart: async (request: CartChangeRequest): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/cart/change`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '修改购物车失败');
    }
  },

  // 删除购物车项目
  deleteCartItem: async (request: CartDeleteRequest): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/cart/delete`, {
      method: 'DELETE',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '删除购物车项目失败');
    }
  },

  // 创建订单
  createOrder: async (request: OrderRequest): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/cart/order`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '创建订单失败');
    }
  },
};

// ==================== 用户认证API ====================

export const authApi = {
  // 用户注册
  register: async (request: RegisterRequest): Promise<void> => {
    const response = await publicFetch(`${API_BASE_URL}/mall/customer/register`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '注册失败');
    }
  },

  // 用户登录
  login: async (request: LoginRequest): Promise<LoginResponse> => {
    const response = await publicFetch(`${API_BASE_URL}/mall/customer/login`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code === 200) {
      setCustomerToken(result.data.token);
      return result.data;
    } else {
      throw new Error(result.message || '登录失败');
    }
  },

  // 用户登出
  logout: async (): Promise<void> => {
    const token = getCustomerToken();
    if (token) {
      try {
        await authenticatedFetch(`${API_BASE_URL}/mall/customer/logout`, {
          method: 'POST',
        });
      } catch (error) {
        console.error('登出请求失败:', error);
      }
    }
    clearCustomerToken();
  },

  // 重置密码（需要旧密码）
  resetPassword: async (request: ResetPasswordRequest): Promise<void> => {
    const response = await publicFetch(`${API_BASE_URL}/mall/customer/reset-password`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '重置密码失败');
    }
  },

  // 忘记密码
  forgotPassword: async (request: ForgotPasswordRequest): Promise<void> => {
    const response = await publicFetch(`${API_BASE_URL}/mall/customer/forgot-password`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '重置密码失败');
    }
  },

  // 获取个人信息（需要登录）
  getProfile: async (): Promise<UserProfile> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/customer/profile`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取个人信息失败');
    }
  },

  // 修改个人信息（需要登录）
  updateProfile: async (data: Partial<UserProfile>): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/customer/profile`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '修改个人信息失败');
    }
  },
};

// ==================== 类型定义 - 地址 ====================

export interface Address {
  id?: number;
  receiver_name: string;
  receiver_phone: string;
  province: string;
  city: string;
  district: string;
  detail: string;
  tag: string;
  is_default: number;
  latitude?: number;
  longitude?: number;
}

// ==================== 类型定义 - 积分 ====================

export interface PointsOverview {
  balance: number;
  frozen: number;
  total_earned: number;
  total_spent: number;
}

export interface PointsLog {
  id: number;
  change_amount: number;
  balance_after: number;
  source_type: number;
  remark: string;
  create_time: string;
}

export interface PointsLogsResponse {
  total: number;
  records: PointsLog[];
}

// ==================== 收货地址API（需要登录） ====================

export const addressApi = {
  // 获取地址列表
  getAddressList: async (): Promise<Address[]> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/address/list`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data || [];
    } else {
      throw new Error(result.message || '获取地址列表失败');
    }
  },

  // 新增地址
  addAddress: async (address: Omit<Address, 'id'>): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/address/add`, {
      method: 'POST',
      body: JSON.stringify(address),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '新增地址失败');
    }
  },

  // 修改地址
  updateAddress: async (address: Address): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/address/update`, {
      method: 'PUT',
      body: JSON.stringify(address),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '修改地址失败');
    }
  },

  // 删除地址
  deleteAddress: async (id: number): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/address/delete/${id}`, {
      method: 'DELETE',
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '删除地址失败');
    }
  },
};

// ==================== 积分API（需要登录） ====================

export const pointsApi = {
  // 积分概览
  getOverview: async (): Promise<PointsOverview> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/points/overview`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取积分概览失败');
    }
  },

  // 积分流水
  getLogs: async (current: number = 1, size: number = 10): Promise<PointsLogsResponse> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/points/logs?current=${current}&size=${size}`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取积分流水失败');
    }
  },
};

// ==================== 类型定义 - 优惠券 ====================

export interface CouponMarket {
  id: number;
  title: string;
  type: number; // 1=满减 2=折扣 3=现金券
  threshold_amount?: number;
  discount_amount?: number;
  discount_rate?: number;
  max_discount?: number;
  valid_from: string;
  valid_to: string;
  is_received: boolean;
}

export interface MyCoupon {
  id: number;
  template_id: number;
  title: string;
  code: string;
  status: number; // 0未使用 1已使用 2已过期 3已作废
  expire_time: string;
  type: number;
  threshold_amount?: number;
  discount_amount?: number;
  discount_rate?: number;
}

// ==================== 类型定义 - 订单 ====================

export interface OrderPreviewItem {
  item_id: number;
  amount: number;
}

export interface OrderPreviewRequest {
  items: OrderPreviewItem[];
  coupon_id?: number;
  use_points?: boolean;
}

export interface OrderPreviewResponse {
  total_price: number;
  delivery_fee: number;
  discount_amount: number;
  points_deduction: number;
  payable_amount: number;
  optimal_coupon?: {
    id: number;
    title: string;
  };
}

export interface OrderCreateRequest {
  address_id: number;
  coupon_id?: number;
  points_used?: number;
  remark?: string;
  items: OrderPreviewItem[];
}

export interface OrderListItem {
  order_no: string;
  status: number;
  payable_amount: number;
  create_time: string;
  items: {
    model: string;
    picture: string;
    amount: number;
  }[];
}

export interface OrderListResponse {
  total: number;
  records: OrderListItem[];
}

export interface OrderDetail {
  id: number;
  order_no: string;
  customer_id: number;
  customer_phone: string;
  order_source: number;
  total_price: number;
  payable_amount: number;
  discount_amount: number;
  dispatch_status: number;
  order_status: number;
  pay_status: number;
  pay_channel?: number;
  pay_time?: string;
  delivery_fee: number;
  coupon_id?: number;
  points_used?: number;
  remark?: string;
  create_time: string;
  receive_time?: string;
  address: {
    receiver_name: string;
    receiver_phone: string;
    province: string;
    city: string;
    district: string;
    detail: string;
  };
  items: {
    id: number;
    item_id: number;
    model: string;
    specification: string;
    selling_price: number;
    amount: number;
    subtotal_price: number;
  }[];
  status_history: {
    from_status?: number;
    to_status: number;
    remark: string;
    create_time: string;
  }[];
}

// ==================== 优惠券API ====================

export const couponApi = {
  // 领券中心（可公开浏览）
  getMarket: async (): Promise<CouponMarket[]> => {
    const response = await publicFetch(`${API_BASE_URL}/mall/coupon/market`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data || [];
    } else {
      throw new Error(result.message || '获取优惠券列表失败');
    }
  },

  // 领取优惠券（需要登录）
  receive: async (templateId: number): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/coupon/receive/${templateId}`, {
      method: 'POST',
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '领取优惠券失败');
    }
  },

  // 我的优惠券（需要登录）
  getMyCoupons: async (status?: number): Promise<MyCoupon[]> => {
    const params = status !== undefined ? `?status=${status}` : '';
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/coupon/my-coupons${params}`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data || [];
    } else {
      throw new Error(result.message || '获取我的优惠券失败');
    }
  },
};

// ==================== 订单API（需要登录） ====================

export const orderApi = {
  // 订单结算预览
  preview: async (request: OrderPreviewRequest): Promise<OrderPreviewResponse> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/order/preview`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取订单预览失败');
    }
  },

  // 创建订单
  create: async (request: OrderCreateRequest): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/order/create`, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '创建订单失败');
    }
  },

  // 订单列表
  getList: async (status?: number, current: number = 1, size: number = 10): Promise<OrderListResponse> => {
    const params = new URLSearchParams();
    if (status !== undefined) params.append('status', status.toString());
    params.append('current', current.toString());
    params.append('size', size.toString());

    const response = await authenticatedFetch(`${API_BASE_URL}/mall/order/list?${params.toString()}`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取订单列表失败');
    }
  },

  // 订单详情
  getDetail: async (orderNo: string): Promise<OrderDetail> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/order/detail/${orderNo}`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取订单详情失败');
    }
  },

  // 取消订单
  cancel: async (orderNo: string, reason?: string): Promise<void> => {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/order/cancel/${orderNo}${params}`, {
      method: 'POST',
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '取消订单失败');
    }
  },

  // 确认收货
  confirm: async (orderNo: string): Promise<{ points_earned: number }> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/order/confirm/${orderNo}`, {
      method: 'POST',
    });

    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '确认收货失败');
    }
  },
};

// ==================== 支付API（需要登录） ====================

export const payApi = {
  // 发起支付
  create: async (orderNo: string, channel: number = 1): Promise<void> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/pay/create`, {
      method: 'POST',
      body: JSON.stringify({ order_no: orderNo, channel }),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '支付失败');
    }
  },

  // 查询支付状态
  getStatus: async (orderNo: string): Promise<{
    order_no: string;
    pay_status: number;
    pay_time?: string;
    transaction_no?: string;
  }> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/pay/status/${orderNo}`);
    const result = await response.json();

    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '查询支付状态失败');
    }
  },
};
