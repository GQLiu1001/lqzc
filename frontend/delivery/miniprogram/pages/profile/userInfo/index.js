// pages/profile/userInfo/index.js
const api = require('../../../utils/api');

Page({

  /**
   * 页面的初始数据
   */
  data: {
    userInfo: {
      name: '',
      phone: '',
      avatar: '',
      auditStatus: 0 // 0: 未审核, 1: 已通过, 2: 被拒绝
    }
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    this.loadUserInfo();
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
  onPullDownRefresh() {

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

  // 加载用户信息
  loadUserInfo() {
    const localUserInfo = wx.getStorageSync('userInfo');
    
    if (localUserInfo && localUserInfo.id) {
      // 直接使用本地存储的用户信息，因为没有获取司机详细信息的API
      this.setData({
        userInfo: {
          name: localUserInfo.name || '',
          phone: localUserInfo.phone || '',
          avatar: localUserInfo.avatar || '',
          audit_status: localUserInfo.audit_status || 0
        }
      });
    }
  },

  // 选择头像
  chooseAvatar() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFilePath = res.tempFilePaths[0];
        
        // 更新头像
        this.setData({
          'userInfo.avatar': tempFilePath
        });
        
        // TODO: 上传头像到服务器
        // 由于后端可能没有支持头像上传功能，这里暂时不实现
      }
    });
  },

  // 输入姓名
  inputDriverName(e) {
    this.setData({
      'userInfo.name': e.detail.value
    });
  },

  // 输入手机号
  inputPhone(e) {
    this.setData({
      'userInfo.phone': e.detail.value
    });
  },

  // 保存用户信息
  saveUserInfo() {
    // 表单验证
    if (!this.data.userInfo.name) {
      return wx.showToast({
        title: '请输入姓名',
        icon: 'none'
      });
    }
    
    if (!this.data.userInfo.phone || !/^1\d{10}$/.test(this.data.userInfo.phone)) {
      return wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
    }
    
    try {
      const localUserInfo = wx.getStorageSync('userInfo');
      
      if (localUserInfo && localUserInfo.id) {
        // 暂时不调用后端接口，因为没有更新司机信息的API，直接更新本地存储
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
        
        // 更新本地存储的用户信息
        localUserInfo.name = this.data.userInfo.name;
        localUserInfo.phone = this.data.userInfo.phone;
        wx.setStorageSync('userInfo', localUserInfo);
        
        // 返回上一页
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      }
    } catch (error) {
      console.error('保存用户信息失败:', error);
      wx.showToast({
        title: '保存失败',
        icon: 'none'
      });
    }
  }
});