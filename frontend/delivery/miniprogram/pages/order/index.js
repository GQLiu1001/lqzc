// pages/order/index.js
const api = require('../../utils/api');
const { formatTime } = require('../../utils/dateUtils');

Page({

  /**
   * 页面的初始数据
   */
  data: {
    orders: [],
    loading: false,
    page: 1,
    hasMore: true,
    isMapPage: false
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    // 检查登录状态
    if (!this.checkLoginStatus()) return;
    
    // 检查token是否存在
    const token = wx.getStorageSync('token');
    if (!token) {
      console.warn('没有token，跳转到登录页');
      wx.reLaunch({
        url: '/pages/login/index'
      });
      return;
    }
    
    // 确保初始化后立即加载数据
    setTimeout(() => {
      this.loadOrders()
    }, 100)
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    // 每次显示页面时刷新订单列表
    this.setData({
      page: 1,
      orders: [],
      hasMore: true
    })
    this.loadOrders()
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {

  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh: function () {
    this.loadOrders()
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {

  },

  
  // 加载订单列表
  loadOrders: function() {
    const token = wx.getStorageSync('token');
    console.log('加载订单时的token:', token);
    
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      wx.reLaunch({
        url: '/pages/login/index'
      });
      return;
    }
    
    wx.showLoading({
      title: '加载中',
    })
    
    // 调用API获取所有订单列表
    console.log('准备调用订单列表API，当前页码:', this.data.page);
    api.getOrderList(this.data.page, 10)
      .then(res => {
        wx.hideLoading()
        wx.stopPullDownRefresh()
        
        console.log('API Response:', JSON.stringify(res));

        if (res.code === 200) {
          const orders = res.data.records || []
          
          console.log('Processed Orders Data:', JSON.stringify(orders));

          // 格式化订单数据
          orders.forEach(order => {
            // 格式化时间 - 使用蛇形字段名，使用日期工具函数确保iOS兼容性
            if (order.create_time) {
              order.formatted_time = formatTime(order.create_time)
            }
            
            // 设置状态文本 - 使用蛇形字段名  
            order.status_text = this.getStatusText(order.dispatch_status)
          })
          
          this.setData({
            orders: this.data.page === 1 ? orders : [...this.data.orders, ...orders],
            hasMore: orders.length === 10,
            page: this.data.page + 1
          })
        } else {
          wx.showToast({
            title: res.message || '获取订单失败',
            icon: 'none'
          })
        }
      })
      .catch(err => {
        console.error('获取订单列表失败:', err)
        wx.hideLoading()
        wx.stopPullDownRefresh()
        wx.showToast({
          title: '获取订单失败',
          icon: 'none'
        })
      })
  },

  // 加载更多订单
  loadMoreOrders() {
    this.loadOrders()
  },



  // 根据状态码获取状态文本
  getStatusText: function(status) {
    const statusMap = {
      1: '待接单',
      2: '已接单', 
      3: '配送中',
      4: '已完成',
      5: '已取消'
    }
    return statusMap[status] || '未知状态'
  },

  // 检查登录状态
  checkLoginStatus() {
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo || !userInfo.id) {
      // 未登录，跳转到登录页面
      wx.reLaunch({
        url: '/pages/login/index'
      });
      return false;
    }
    return true;
  }
})