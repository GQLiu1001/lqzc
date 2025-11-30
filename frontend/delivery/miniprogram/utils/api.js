const { config } = require('./config');

// API路径 - 根据新的接口文档更新
const API = {
  // 司机相关
  driver: {
    login: `${config.apiBaseUrl}/driver/login`,
    auditStatus: `${config.apiBaseUrl}/driver/audit-status/:id`,
    logout: `${config.apiBaseUrl}/driver/logout`,
    changeStatus: `${config.apiBaseUrl}/driver/info/change-status/:id/:status`,
    wallet: `${config.apiBaseUrl}/driver/info/wallet/:id`,
    updateLocation: `${config.apiBaseUrl}/driver/info/update-location`
  },
  // 订单相关
  delivery: {
    list: `${config.apiBaseUrl}/delivery/list`,
    fetch: `${config.apiBaseUrl}/delivery/fetch/:status`,
    rob: `${config.apiBaseUrl}/delivery/rob/:id/:orderNo`,
    complete: `${config.apiBaseUrl}/delivery/complete/:orderNo`,
    cancel: `${config.apiBaseUrl}/delivery/cancel/:orderNo`
  },
  // 腾讯地图
  route: `${config.apiBaseUrl}/route`
};

// 替换URL中的参数
const formatUrl = (url, params) => {
  let formattedUrl = url;
  if (params) {
    Object.keys(params).forEach(key => {
      formattedUrl = formattedUrl.replace(`:${key}`, params[key]);
    });
  }
  return formattedUrl;
};

// 处理请求头
const getHeaders = () => {
  const token = wx.getStorageSync('token');
  console.log('当前token:', token);
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
};

// 封装请求方法
const request = (url, method, data, params) => {
  const formattedUrl = formatUrl(url, params);
  
  return new Promise((resolve, reject) => {
    wx.request({
      url: formattedUrl,
      method,
      data,
      header: getHeaders(),
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          if (res.statusCode === 401) {
            wx.removeStorageSync('token');
            wx.removeStorageSync('userInfo');
            wx.reLaunch({
              url: '/pages/login/index'
            });
          }
          reject(new Error(`请求失败: ${res.statusCode} ${res.data.message || ''}`));
        }
      },
      fail: (err) => {
        reject(new Error(`网络请求失败: ${err.errMsg}`));
      }
    });
  });
};

// 导出API方法 - 根据新的接口文档更新
module.exports = {
  // 司机登录
  login: (code, phone) => {
    const url = `${API.driver.login}?code=${code}&phone=${phone}`;
    return request(url, 'POST', null);
  },
  
  // 获取司机审核状态
  getAuditStatus: (id) => {
    return request(API.driver.auditStatus, 'GET', null, { id });
  },
  
  // 司机登出
  logout: () => {
    return request(API.driver.logout, 'GET', null);
  },
  
  // 更新司机状态
  changeDriverStatus: (id, status) => {
    return request(API.driver.changeStatus, 'POST', null, { id, status });
  },
  
  // 获取钱包信息
  getWallet: (id) => {
    return request(API.driver.wallet, 'GET', null, { id });
  },
  
  // 更新司机经纬度地址
  updateLocation: (id, latitude, longitude) => {
    const url = `${API.driver.updateLocation}?id=${id}&latitude=${latitude}&longitude=${longitude}`;
    return request(url, 'POST', null);
  },
  
  // 腾讯地图路线规划
  getRoute: (fromLat, fromLng, toLat, toLng) => {
    console.log('调用路线规划API:', { fromLat, fromLng, toLat, toLng });
    const url = `${API.route}?fromLat=${fromLat}&toLat=${toLat}&fromLng=${fromLng}&toLng=${toLng}`;
    return request(url, 'GET', null);
  },
  
  // 获取订单列表
  getOrderList: (current, size) => {
    const url = `${API.delivery.list}?current=${current}&size=${size}`;
    return request(url, 'GET', null);
  },

  // 获取可派送订单
  getAvailableOrders: (status, current, size) => {
    const url = `${API.delivery.fetch}?current=${current}&size=${size}`;
    return request(url, 'GET', null, { status });
  },
  
  // 司机抢单
  robOrder: (id, order_no) => {
    return request(API.delivery.rob, 'POST', null, { id, orderNo: order_no });
  },
  
  // 完成订单
  completeOrder: (order_no) => {
    return request(API.delivery.complete, 'POST', null, { orderNo: order_no });
  },
  
  // 取消订单
  cancelOrder: (order_no) => {
    return request(API.delivery.cancel, 'POST', null, { orderNo: order_no });
  }
}; 