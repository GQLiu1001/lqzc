const api = require('../../utils/api');

Page({
  data: {
    isLogin: false,
    userInfo: null,
    defaultAvatar: '/miniprogram/assets/images/default-avatar.png',
    balance: 0,
    totalIncome: 0,
    name: '',
    phone: '',
    vehicleNo: '',
    vehicleType: '',
    idCard: '',
    avatar: '',
    editDialogVisible: false,
    editName: '',
    editPhone: '',
    editVehicleNo: '',
    editVehicleType: '',
    editIdCard: ''
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow: function () {
    this.fetchUserInfo()
    this.fetchWallet()
  },

  // 获取用户信息
  fetchUserInfo: function() {
    // 检查本地存储中是否有token和用户信息
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    
    if (!token || !userInfo) {
      // 未登录状态
      this.setData({
        isLogin: false,
        userInfo: null
      })
      return
    }
    
    // 直接使用本地存储的用户信息
    this.setData({
      isLogin: true,
      userInfo: userInfo,
      name: userInfo.name || '',
      phone: userInfo.phone || '',
      vehicleNo: userInfo.vehicle_no || '',
      vehicleType: userInfo.vehicle_type || '',
      idCard: userInfo.id_card || '',
      avatar: userInfo.avatar || this.data.defaultAvatar
    })
  },

  // 获取钱包信息
  fetchWallet: function() {
    // 检查是否登录
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    
    if (!token || !userInfo || !userInfo.id) return
    
    // 调用获取钱包API
    api.getWallet(userInfo.id)
      .then(res => {
        if (res.code === 200) {
          // 更新钱包信息
          this.setData({
            balance: res.data || 0,
            totalIncome: res.data || 0
          })
        }
      })
      .catch(err => {
        console.error('获取钱包信息失败:', err)
        // 不显示错误提示，避免影响体验
      })
  },

  // 前往登录页
  goToLogin: function() {
    wx.navigateTo({
      url: '/miniprogram/pages/login/index'
    })
  },

  // 前往钱包页面
  goToWallet: function() {
    if (!this.data.isLogin) {
      this.goToLogin()
      return
    }
    
    wx.navigateTo({
      url: '/miniprogram/pages/wallet/index'
    })
  },

  // 打开编辑信息对话框
  openEditDialog: function() {
    this.setData({
      editDialogVisible: true,
      editName: this.data.name,
      editPhone: this.data.phone,
      editVehicleNo: this.data.vehicleNo,
      editVehicleType: this.data.vehicleType,
      editIdCard: this.data.idCard
    })
  },

  // 关闭编辑对话框
  closeEditDialog: function() {
    this.setData({
      editDialogVisible: false
    })
  },

  // 处理输入变化
  onInputChange: function(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    
    const data = {}
    data['edit' + field.charAt(0).toUpperCase() + field.slice(1)] = value
    
    this.setData(data)
  },

  // 保存用户信息
  saveUserInfo: function() {
    // 构建更新数据对象
    const updateData = {
      name: this.data.editName,
      phone: this.data.editPhone,
      vehicle_no: this.data.editVehicleNo,
      vehicle_type: this.data.editVehicleType,
      id_card: this.data.editIdCard
    }
    
    // 显示加载中
    wx.showLoading({
      title: '保存中',
    })
    
    // 暂时不调用后端API，直接更新本地存储
    wx.hideLoading()
    
    // 更新本地数据
    this.setData({
      name: updateData.name,
      phone: updateData.phone,
      vehicleNo: updateData.vehicle_no,
      vehicleType: updateData.vehicle_type,
      idCard: updateData.id_card,
      userInfo: {
        ...this.data.userInfo,
        ...updateData
      },
      editDialogVisible: false
    })
    
    // 保存到本地存储
    wx.setStorageSync('userInfo', this.data.userInfo)
    
    wx.showToast({
      title: '保存成功',
      icon: 'success'
    })
  },

  // 退出登录
  logout: function() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 获取用户信息准备调用登出API
          const userInfo = wx.getStorageSync('userInfo')
          
          if (userInfo && userInfo.id) {
            // 调用登出API
            api.logout(userInfo.id)
              .then(() => {
                // 清除本地存储
                wx.removeStorageSync('token')
                wx.removeStorageSync('userInfo')
                
                // 更新状态
                this.setData({
                  isLogin: false,
                  userInfo: null,
                  balance: 0,
                  totalIncome: 0
                })
                
                wx.showToast({
                  title: '已退出登录',
                  icon: 'success'
                })
                
                // 跳转到登录页
                setTimeout(() => {
                  wx.reLaunch({
                    url: '/pages/login/index'
                  })
                }, 1000)
              })
              .catch(err => {
                console.error('退出登录失败:', err)
                // 即使API调用失败，仍然清除本地数据
                wx.removeStorageSync('token')
                wx.removeStorageSync('userInfo')
                
                this.setData({
                  isLogin: false,
                  userInfo: null
                })
                
                wx.showToast({
                  title: '已退出登录',
                  icon: 'success'
                })
                
                // 跳转到登录页
                setTimeout(() => {
                  wx.reLaunch({
                    url: '/pages/login/index'
                  })
                }, 1000)
              })
          } else {
            // 没有用户信息，直接清除本地数据
            wx.removeStorageSync('token')
            wx.removeStorageSync('userInfo')
            
            this.setData({
              isLogin: false,
              userInfo: null
            })
            
            wx.reLaunch({
              url: '/pages/login/index'
            })
          }
        }
      }
    })
  }
}) 