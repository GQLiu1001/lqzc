// 生产环境API地址 - 使用nginx代理路径
const API_BASE_URL = '/api';

// 如果需要切换回开发环境，请将上面的地址改为：'/api'

// 存储匿名token的localStorage键名
const TOKEN_STORAGE_KEY = 'mall_anonymous_token';

// 强制从后端获取新匿名token并存储
export const refreshAnonymousToken = async (): Promise<string> => {
  try {
    // 首先清除可能存在的旧token，以防万一
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    
    const response = await fetch(`${API_BASE_URL}/mall/auth/anonymous-token`);
    const result = await response.json();
    
    if (result.code === 200) {
      // 将新token存储到localStorage
      localStorage.setItem(TOKEN_STORAGE_KEY, result.data);
      return result.data;
    } else {
      throw new Error(result.message || '获取新token失败');
    }
  } catch (error) {
    console.error('刷新匿名token失败:', error);
    throw error;
  }
};

// 获取匿名token
export const getAnonymousToken = async (): Promise<string> => {
  // 先检查localStorage中是否有token
  const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (storedToken) {
    return storedToken;
  }
  // 如果没有，则获取新token
  return refreshAnonymousToken();
};

// 清除token（可用于重置购物车）
export const clearAnonymousToken = () => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};

// 创建带认证的fetch请求
const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
  const doFetch = async (token: string) => {
    return fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });
  };

  let token = await getAnonymousToken();
  let response = await doFetch(token);

  // 如果响应是401 (Unauthorized)，则认为token过期，刷新token并重试一次
  if (response.status === 401) {
    console.warn('收到401响应，匿名token可能已过期，正在尝试刷新...');
    
    try {
      const newToken = await refreshAnonymousToken();
      console.log('匿名token刷新成功，正在重试原始请求...');
      response = await doFetch(newToken);
    } catch (refreshError) {
      console.error('刷新token失败，无法重试请求。', refreshError);
      // 如果刷新失败，直接返回原始的401响应，让上层逻辑处理
      return response;
    }
  }

  return response;
};

// 产品接口类型定义
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

// 购物车接口类型定义
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

// 表面处理和分类映射
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

// 反向映射
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

// API方法
export const mallApi = {
  // 获取商品列表
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
    
    const response = await authenticatedFetch(
      `${API_BASE_URL}/mall/items/list?${queryParams.toString()}`
    );
    
    const result = await response.json();
    
    if (result.code === 200) {
      return result.data;
    } else {
      throw new Error(result.message || '获取商品列表失败');
    }
  },

  // 查看购物车
  getCart: async (): Promise<CartItem[]> => {
    const response = await authenticatedFetch(`${API_BASE_URL}/mall/cart`);
    const result = await response.json();
    
    if (result.code === 200) {
      // 安全处理返回的数据，确保返回数组
      if (result.data === null || result.data === undefined) {
        return [];
      }
      if (Array.isArray(result.data)) {
        return result.data;
      }
      // 如果不是数组，返回空数组
      return [];
    } else {
      throw new Error(result.message || '获取购物车失败');
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