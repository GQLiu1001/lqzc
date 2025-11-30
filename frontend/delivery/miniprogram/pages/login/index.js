// pages/login/index.js
const api = require('../../utils/api');

Page({
  data: {
    phone: '',
    isSubmitting: false,
    auditStatus: null, // null=未登录, 0=未审核, 1=已通过, 2=已拒绝
  },

  onLoad() {
    // 检查登录状态
    this.checkLoginStatus();
  },

  // 检查登录状态
  async checkLoginStatus() {
    try {
      // 从本地存储获取用户信息
      const userInfo = wx.getStorageSync('userInfo');
      
      if (userInfo && userInfo.id) {
        // 如果已登录，则获取审核状态
        const res = await api.getAuditStatus(userInfo.id);
        
        if (res.code === 200) {
          const auditStatus = res.data;
          
          if (auditStatus === 1) {
            // 已审核通过，直接跳转到首页
            wx.reLaunch({
              url: '/pages/map/index'
            });
          } else {
            // 设置审核状态
            this.setData({ auditStatus });
          }
        }
      }
    } catch (error) {
      console.error('检查登录状态失败:', error);
    }
  },

  // 输入框内容变化
  handleInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({
      [field]: e.detail.value
    });
  },

  // 处理登录
  async handleLogin() {
    try {
      if (this.data.isSubmitting) return;
      
      // 表单验证
      if (!this.data.phone) {
        wx.showToast({
          title: '请输入手机号',
          icon: 'none'
        });
        return;
      }
      
      this.setData({ isSubmitting: true });
      
      // 获取微信登录凭证
      const { code } = await wx.login();
      
      // 调用后端登录接口
      const res = await api.login(code, this.data.phone);
      
      if (res.code === 200) {
        // 保存token和用户信息到本地
        console.log('登录成功，完整响应数据:', res.data);
        const token = res.data.token;
        if (token) {
          wx.setStorageSync('token', token);
          console.log('Token保存成功:', token);
        } else {
          console.warn('响应中没有token字段');
        }
        
        // 创建用户信息对象（使用后端返回的蛇形命名字段）
        const userInfo = {
          id: res.data.id,
          name: res.data.name,
          phone: res.data.phone,
          avatar: res.data.avatar,
          audit_status: res.data.audit_status,
          work_status: res.data.work_status,
          money: res.data.money
        };
        wx.setStorageSync('userInfo', userInfo);
        
        // 判断审核状态
        if (res.data.audit_status === 1) {
          // 已审核通过，跳转到首页
          wx.reLaunch({
            url: '/pages/map/index'
          });
        } else {
          // 设置审核状态
          this.setData({ 
            auditStatus: res.data.audit_status || 0,  // 默认值避免undefined
            isSubmitting: false
          });
        }
      } else {
        wx.showToast({
          title: res.message || '登录失败，请检查手机号',
          icon: 'none'
        });
        this.setData({ isSubmitting: false });
      }
    } catch (error) {
      console.error('登录失败:', error);
      wx.showToast({
        title: '登录失败，请重试',
        icon: 'none'
      });
      this.setData({ isSubmitting: false });
    }
  }
}); 