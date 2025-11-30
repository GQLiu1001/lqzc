const api = require('../../../utils/api');

Page({
  data: {
    balance: 0.00
  },

  onLoad: function() {
    this.loadWalletInfo();
  },

  onPullDownRefresh: function() {
    this.loadWalletInfo();
    wx.stopPullDownRefresh();
  },

  // 加载钱包信息
  loadWalletInfo: function() {
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo || !userInfo.id) {
      return;
    }
    
    wx.showLoading({
      title: '加载中',
    });
    
    api.getWallet(userInfo.id)
      .then(res => {
        wx.hideLoading();
        
        if (res.code === 200) {
          // 设置钱包余额
          this.setData({
            balance: res.data || 0.00
          });
        } else {
          wx.showToast({
            title: res.message || '获取余额失败',
            icon: 'none'
          });
        }
      })
      .catch(err => {
        wx.hideLoading();
        console.error('获取钱包余额失败:', err);
        wx.showToast({
          title: '获取余额失败',
          icon: 'none'
        });
      });
  }
}) 