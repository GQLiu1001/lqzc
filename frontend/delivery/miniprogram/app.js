// app.js
// 引入配置文件
const { config } = require('./utils/config');

App({
  onLaunch: function () {
    // 初始化全局数据
    this.globalData = {
      userInfo: null,
      // 默认启用地图API调用
      enableMapApiCalls: true,
      // 地图API调用间隔(毫秒)
      mapApiCallInterval: 5000,
      // 最后一次调用地图API的时间戳
      lastMapApiCallTime: {}
    }

    // 检查登录状态
    this.checkLoginStatus();
    
    console.log('当前使用的地图密钥:', config.mapKey);
  },

  // 检查是否可以调用特定地图API
  canCallMapApi: function(apiName) {
    const now = Date.now();
    const lastCallTime = this.globalData.lastMapApiCallTime[apiName] || 0;
    
    // 如果距离上次调用时间小于设定的间隔，则不允许调用
    if (now - lastCallTime < this.globalData.mapApiCallInterval) {
      return false;
    }
    
    // 更新最后调用时间
    this.globalData.lastMapApiCallTime[apiName] = now;
    return true;
  },

  // 检查登录状态
  checkLoginStatus: function() {
    const userInfo = wx.getStorageSync('userInfo');
    if (userInfo) {
      this.globalData.userInfo = userInfo;
    }
  }
});
