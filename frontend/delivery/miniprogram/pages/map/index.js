const app = getApp()
// 引入地图选点插件
const chooseLocation = requirePlugin('chooseLocation');
// 引入API模块
const api = require('../../utils/api');
// 引入配置模块
const { config } = require('../../utils/config');
// 引入腾讯地图SDK
const QQMapWX = require('../../lib/qqmap-wx-jssdk.min.js');
// 实例化腾讯地图SDK
const qqmapsdk = new QQMapWX({
  key: config.mapKey // 从配置文件中获取API密钥
});

Page({
  data: {
    longitude: 113.264435, // 默认经度（广州）
    latitude: 23.129163,   // 默认纬度
    scale: 14,
    markers: [],
    polyline: [],
    isOnline: false,
    currentOrder: null,
    locationUpdateTimer: null,
    // 状态和路线信息
    deliveryStatus: '空闲',
    orderStatus: '',
    customerPhone: '',
    customerAddress: '',
    routeDistance: '0.0',
    routeTime: '0',
    nextActionText: '接单',
    // 是否显示位置选择按钮
    showLocationPicker: false,
    // 新订单相关
    newOrderVisible: false,
    newOrder: null,
    lastGeocoderCalls: {},
    orderPollingTimer: null,
    // 倒计时相关
    countdown: 10,
    countdownTimer: null
  },

  onLoad() {
    this.initLocation()
    this.checkLoginStatus()
    
    // 监听新订单
    this.setupOrderListener()
  },

  // 获取司机状态文本
  getDriverStatusText(status) {
    const statusMap = {
      0: '空闲',
      1: '忙碌', 
      2: '离线'
    }
    return statusMap[status] || '未知状态'
  },

  // 统一更新司机状态的方法
  updateDriverStatus(status, successMessage) {
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo || !userInfo.id) return Promise.reject('用户信息不存在');

    return api.changeDriverStatus(userInfo.id, status)
      .then(() => {
        console.log(`司机状态更新为${this.getDriverStatusText(status)}`);
        if (successMessage) {
          wx.showToast({
            title: successMessage,
            icon: 'success'
          });
        }
      })
      .catch(err => {
        console.error('更新司机状态失败:', err);
        throw err;
      });
  },

  onShow() {
    if (this.data.isOnline) {
      this.startLocationUpdate()
    }
    
    // 获取从地图选点插件返回的位置信息
    const location = chooseLocation.getLocation();
    if (location) {
      console.log('选择的位置:', location);
      
      // 由于API配额限制，直接使用选点返回的位置信息
      // 不再额外调用反向地址解析
      // 注释掉模拟订单创建
      // if (!this.data.currentOrder) {
      //   // 如果没有当前订单，可以创建一个新订单使用选择的位置
      //   this.createOrderWithLocation(location);
      // }
    }
  },

  onHide() {
    this.stopLocationUpdate()
  },

  onUnload() {
    this.stopLocationUpdate()
    // 清除订单轮询定时器
    if (this.orderPollingTimer) {
      clearInterval(this.orderPollingTimer);
      this.orderPollingTimer = null;
    }
    // 清除倒计时定时器
    this.clearCountdown();
    // 页面卸载时，需要取消位置选点
    chooseLocation.setLocation(null);
  },

  // 初始化位置
  async initLocation() {
    try {
      const location = await this.getCurrentLocation()
      this.setData({
        latitude: location.latitude,
        longitude: location.longitude
      })
      
      // 由于API配额限制，开发阶段不每次都调用反向地址解析
      // 在生产环境或需要时才调用
      if (app.globalData && app.globalData.enableMapApiCalls) {
        this.reverseGeocoder(location.latitude, location.longitude);
      }
    } catch (error) {
      wx.showToast({
        title: '获取位置失败',
        icon: 'none'
      })
    }
  },

  // 获取当前位置
  getCurrentLocation() {
    return new Promise((resolve, reject) => {
      wx.getLocation({
        type: 'gcj02',
        success: resolve,
        fail: reject
      })
    })
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
  },

  // 设置订单监听器（模拟服务器推送）
  setupOrderListener() {
    // 实际项目中，这里应该连接WebSocket或其他消息推送服务
    // 立即获取一次新订单
    if (this.data.isOnline && !this.data.currentOrder) {
      this.getNewOrders();
    }
    
    // 每60秒轮询一次新订单接口
    this.orderPollingTimer = setInterval(() => {
      if (this.data.isOnline && !this.data.currentOrder) {
        this.getNewOrders();
      }
    }, 15000); // 60秒轮询一次
  },
  
  // 接收新订单
  receiveNewOrder(order) {
    this.setData({
      newOrder: order,
      newOrderVisible: true,
      countdown: 10
    })
    
    // 播放提示音
    const innerAudioContext = wx.createInnerAudioContext()
    innerAudioContext.src = '/audio/new_order.mp3'
    innerAudioContext.play()
    
    // 开始10秒倒计时
    this.startCountdown();
  },

  // 开始倒计时
  startCountdown() {
    // 清除之前的倒计时
    if (this.data.countdownTimer) {
      clearInterval(this.data.countdownTimer);
    }
    
    const timer = setInterval(() => {
      const newCountdown = this.data.countdown - 1;
      this.setData({
        countdown: newCountdown
      });
      
      if (newCountdown <= 0) {
        // 倒计时结束，自动拒绝订单
        clearInterval(timer);
        this.setData({
          countdownTimer: null
        });
        this.autoRejectOrder();
      }
    }, 1000);
    
    this.setData({
      countdownTimer: timer
    });
  },

  // 自动拒绝订单
  autoRejectOrder() {
    console.log('倒计时结束，自动拒绝订单');
    const currentTime = Date.now();
    this.setData({
      newOrderVisible: false,
      newOrder: null,
      countdown: 10,
      lastRejectTime: currentTime
    });
    
    wx.showToast({
      title: '超时未响应，已自动拒绝',
      icon: 'none'
    });
    
    console.log('设置冷却时间，30秒内不会再推送新订单');
  },

  // 清除倒计时
  clearCountdown() {
    if (this.data.countdownTimer) {
      clearInterval(this.data.countdownTimer);
      this.setData({
        countdownTimer: null,
        countdown: 10
      });
    }
  },
  
  // 接受订单
  acceptOrder() {
    if (!this.data.newOrder) return
    
    // 清除倒计时
    this.clearCountdown();
    
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo || !userInfo.id) {
      wx.showToast({
        title: '用户信息不完整，请重新登录',
        icon: 'none'
      });
      return;
    }
    
    console.log('准备接单，订单数据:', this.data.newOrder);
    
    // 获取当前位置
    this.getCurrentLocation().then(location => {
      console.log('当前位置:', location);

      // 确保订单有配送地址坐标 - 使用蛇形字段名
      if (!this.data.newOrder.delivery_latitude || !this.data.newOrder.delivery_longitude) {
        console.log('订单使用默认坐标（上海市中心）');
        this.data.newOrder.delivery_latitude = 31.230416;
        this.data.newOrder.delivery_longitude = 121.473701;
      }

      // 直接进行抢单
      this.doAcceptOrder(userInfo.id);
      
    }).catch(err => {
      console.error('获取位置失败:', err);
      wx.showToast({
        title: '获取位置失败，请允许位置权限',
        icon: 'none'
      });
    });
  },
  
  // 执行抢单操作
  doAcceptOrder(userId) {
    console.log('开始执行抢单操作，用户ID:', userId);
    // 调用后端接口抢单
    api.robOrder(
      userId,
      this.data.newOrder.order_no
    )
    .then(res => {
      console.log('抢单接口返回:', res);
      if (res.code === 200) {
        // 抢单成功，确保保存完整的订单信息，包括经纬度 - 使用蛇形字段名
        const currentOrder = {
          ...this.data.newOrder,
          // 确保记录经纬度信息
          delivery_latitude: this.data.newOrder.delivery_latitude,
          delivery_longitude: this.data.newOrder.delivery_longitude
        };
        
        console.log('抢单成功，保存的订单数据:', currentOrder);
        
        // 更新当前订单 - 使用蛇形字段名
        this.setData({
          currentOrder: currentOrder,
          newOrderVisible: false,
          newOrder: null,
          deliveryStatus: '配送中',
          orderStatus: '已接单',
          customerPhone: currentOrder.customer_phone,
          customerAddress: currentOrder.delivery_address,
          nextActionText: '完成配送',
          lastRejectTime: 0 // 清除冷却时间
        });

        // 抢单成功后更新司机状态为忙碌 (1=忙碌)
        this.updateDriverStatus(1).catch(err => {
          console.error('更新司机状态失败:', err);
        });

        // 显示接单成功提示
        wx.showToast({
          title: '抢单成功',
          icon: 'success'
        });

        // 确保在setData完成后再调用路线规划
        setTimeout(() => {
          console.log('开始规划路线，当前订单数据:', this.data.currentOrder);
          console.log('当前位置数据:', {
            latitude: this.data.latitude,
            longitude: this.data.longitude
          });
          
          // 直接调用doRefreshRoute，传入正确的坐标 - 使用蛇形字段名
          this.doRefreshRoute(
            this.data.currentOrder.delivery_latitude,
            this.data.currentOrder.delivery_longitude
          );
        }, 100);
      } else {
        wx.showToast({
          title: res.message || '抢单失败',
          icon: 'none'
        });
        // 重置状态并隐藏新订单弹窗
        this.setData({
          newOrderVisible: false,
          newOrder: null
        });
      }
    })
    .catch(err => {
      console.error('抢单失败:', err);
      wx.showToast({
        title: '抢单失败，请重试',
        icon: 'none'
      });
    });
  },
  
  // 拒绝订单
  rejectOrder() {
    // 清除倒计时
    this.clearCountdown();
    
    // 手动拒绝设置较短的冷却时间（10秒）
    const currentTime = Date.now();
    this.setData({
      newOrderVisible: false,
      newOrder: null,
      lastRejectTime: currentTime - (this.data.rejectCooldown - 10000) // 只冷却10秒
    })
    
    // 目前API没有专门的拒绝订单接口，可能需要通过取消订单实现
    // if (this.data.newOrder && this.data.newOrder.id) {
    //   api.cancelOrder(this.data.newOrder.id, '司机拒绝接单')
    //     .then(() => {
    //       console.log('拒绝订单成功');
    //     })
    //     .catch(err => {
    //       console.error('拒绝订单失败:', err);
    //     });
    // }
    
    wx.showToast({
      title: '已拒绝订单',
      icon: 'none'
    })
    
    console.log('手动拒绝订单，设置10秒冷却时间');
  },

  // 切换在线状态
  toggleOnlineStatus(e) {
    const isOnline = e.detail.value
    this.setData({ isOnline })

    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo || !userInfo.id) return;

    if (isOnline) {
      this.startLocationUpdate()
      // 更新司机状态为空闲 (0=空闲)
      this.updateDriverStatus(0, '已上线')
        .then(() => {
          // 获取新订单
          this.getNewOrders();
          
          // 如果定时器未开启，重新开启定时器
          if (!this.orderPollingTimer) {
            this.setupOrderListener();
          }
        })
        .catch(err => {
          console.error('上线失败:', err);
        });
    } else {
      this.stopLocationUpdate()
      // 更新司机状态为离线 (2=离线)
      this.updateDriverStatus(2, '已下线')
        .then(() => {
          // 清除订单轮询定时器
          if (this.orderPollingTimer) {
            clearInterval(this.orderPollingTimer);
            this.orderPollingTimer = null;
          }
        })
        .catch(err => {
          console.error('下线失败:', err);
        });
    }
  },

  // 开始定时更新位置
  startLocationUpdate() {
    if (this.data.locationUpdateTimer) return
    
    const updateLocation = async () => {
      try {
        const location = await this.getCurrentLocation()
        this.setData({
          latitude: location.latitude,
          longitude: location.longitude
        })
        
        // 更新司机位置到后端
        this.updateDriverLocation(location)
        
        // 如果有当前订单，刷新路线
        if (this.data.currentOrder) {
          this.refreshRoute()
        }
      } catch (error) {
        console.error('更新位置失败', error)
      }
    }
    
    // 立即执行一次
    updateLocation()
    // 设置30秒更新一次位置
    this.data.locationUpdateTimer = setInterval(updateLocation, 30000)
  },

  // 停止定时更新位置
  stopLocationUpdate() {
    if (this.data.locationUpdateTimer) {
      clearInterval(this.data.locationUpdateTimer)
      this.data.locationUpdateTimer = null
    }
  },

  // 更新司机位置到后端
  async updateDriverLocation(location) {
    try {
      const userInfo = wx.getStorageSync('userInfo');
      if (userInfo && userInfo.id) {
        await api.updateLocation(
          userInfo.id,
          location.latitude,
          location.longitude
        );
        console.log('位置更新成功');
      }
    } catch (error) {
      console.error('位置更新失败', error);
    }
  },

  // 取消所有订单
  cancelAllOrders() {
    wx.showModal({
      title: '确认操作',
      content: '确定要撤销当前订单吗？',
      success: (res) => {
        if (res.confirm) {
          // 调用后端接口取消订单
          if (this.data.currentOrder && this.data.currentOrder.order_no) {
            api.cancelOrder(this.data.currentOrder.order_no)
              .then(res => {
                if (res.code === 200) {
                  // 清除当前订单信息
                  this.setData({
                    currentOrder: null,
                    deliveryStatus: '空闲',
                    orderStatus: '',
                    customerPhone: '',
                    customerAddress: '',
                    routeDistance: '0.0',
                    routeTime: '0',
                    nextActionText: '接单',
                    markers: [],
                    polyline: []
                  });
                  
                  // 取消订单后更新司机状态为空闲 (0=空闲)
                  this.updateDriverStatus(0).catch(err => {
                    console.error('更新司机状态失败:', err);
                  });
                  
                  wx.showToast({
                    title: '已撤销订单',
                    icon: 'success'
                  });
                } else {
                  wx.showToast({
                    title: res.message || '取消订单失败',
                    icon: 'none'
                  });
                }
              })
              .catch(err => {
                console.error('取消订单失败:', err);
                wx.showToast({
                  title: '取消订单失败',
                  icon: 'none'
                });
              });
          }
        }
      }
    });
  },

  // 刷新路线规划
  refreshRoute() {
    console.log('进入refreshRoute函数');
    if (!this.data.currentOrder) {
      console.log('没有当前订单，不进行路线规划');
      return;
    }
    
    console.log('开始刷新路线，当前订单:', this.data.currentOrder);
    console.log('当前位置:', {
      latitude: this.data.latitude,
      longitude: this.data.longitude
    });

    // 直接使用订单中的坐标
    const destLat = this.data.currentOrder.delivery_latitude;
    const destLng = this.data.currentOrder.delivery_longitude;
    
    console.log('即将调用doRefreshRoute，目的地坐标:', {
      destLat,
      destLng
    });
    
    this.doRefreshRoute(destLat, destLng);
  },
  
  // 使用默认位置进行路线规划
  handleRouteWithDefaultLocation() {
    wx.showToast({
      title: '无法获取目的地位置，请重试',
      icon: 'none',
      duration: 2000
    });
    
    // 提示用户操作失败，不再使用默认坐标
    wx.showModal({
      title: '地址解析失败',
      content: '无法获取配送地址的坐标信息，请联系管理员更新地址信息',
      showCancel: false
    });
    
    // 不再继续路线规划
    if (this.data.currentOrder) {
      this.setData({
        polyline: [],
        markers: []
      });
    }
  },
  
  // 实际执行路线规划
  doRefreshRoute(destLat, destLng) {
    console.log('进入doRefreshRoute，参数:', { destLat, destLng });
    console.log('当前订单数据:', this.data.currentOrder);
    console.log('当前位置:', {
      latitude: this.data.latitude,
      longitude: this.data.longitude
    });
    
    if (!destLat || !destLng) {
      console.error('目的地坐标无效');
      wx.showToast({
        title: '无法获取配送地址坐标',
        icon: 'none'
      });
      return;
    }

    if (!this.data.latitude || !this.data.longitude) {
      console.error('当前位置坐标无效');
      wx.showToast({
        title: '无法获取当前位置',
        icon: 'none'
      });
      return;
    }

    try {
      const params = {
        fromLat: this.data.latitude,
        fromLng: this.data.longitude,
        toLat: destLat,
        toLng: destLng
      };
      
      console.log('准备调用路线规划API，完整参数:', params);
      console.log('API调用URL将包含参数:',
        `fromLat=${params.fromLat}`,
        `fromLng=${params.fromLng}`,
        `toLat=${params.toLat}`,
        `toLng=${params.toLng}`
      );

      // 调用后端路线规划API
      api.getRoute(
        params.fromLat,
        params.fromLng,
        params.toLat,
        params.toLng
      )
      .then(res => {
        console.log('后端路线规划返回:', res);
        
        if (res.code === 200) {
          const routeData = res.data;
          console.log('路线数据:', routeData);
          
          if (routeData && routeData.polyline) {
            // 处理路线数据
            this.renderRouteFromBackend(routeData);
            
            // 更新距离和时间信息
            const durationText = `${routeData.duration}分钟`;
            this.setData({
              routeDistance: routeData.distance ? (routeData.distance / 1000).toFixed(1) : '0.0',
              routeTime: durationText
            });
          } else {
            console.warn('路线数据中没有polyline:', routeData);
            this.handleRouteError();
          }
        } else {
          console.warn('后端路线规划接口返回错误:', res.message);
          this.handleRouteError();
        }
      })
      .catch(err => {
        console.error('调用后端路线规划接口失败:', err);
        this.handleRouteError();
      });
    } catch (error) {
      console.error('路线规划失败:', error);
      this.handleRouteError();
    }
  },
  
  // 处理路线规划错误
  handleRouteError() {
    // 使用简单路线作为后备方案
    if (this.data.currentOrder) {
      this.renderSimpleRoute({
        from: {
          latitude: this.data.latitude,
          longitude: this.data.longitude
        },
        to: {
          latitude: this.data.currentOrder.deliveryLatitude,
          longitude: this.data.currentOrder.deliveryLongitude
        }
      });
      
      // 计算简单的距离和时间估计
      const distance = this.calculateDistance(
        this.data.latitude,
        this.data.longitude,
        this.data.currentOrder.delivery_latitude,
        this.data.currentOrder.delivery_longitude
      );
      
      const distanceKm = (distance / 1000).toFixed(1);
      const timeMinutes = this.estimateDuration(distance);
      
      this.setData({
        routeDistance: distanceKm,
        routeTime: timeMinutes
      });
    }
  },
  
  // 正确处理后端返回的路线数据
  renderRouteFromBackend(routeData) {
    let points = [];
    
    if (routeData.polyline && Array.isArray(routeData.polyline)) {
      // 后端返回的polyline格式为[[lng,lat], [lng,lat], ...]
      points = routeData.polyline.map(point => ({
        longitude: point[0],  // 经度
        latitude: point[1]    // 纬度
      }));
    }
    
    // 如果没有足够的路线点，使用简单路线
    if (points.length < 2) {
      console.warn('未能从后端获取有效路线数据，使用简单路线');
      this.renderSimpleRoute({
        from: {
          latitude: this.data.latitude,
          longitude: this.data.longitude
        },
        to: {
          latitude: this.data.currentOrder.deliveryLatitude,
          longitude: this.data.currentOrder.deliveryLongitude
        }
      });
      return;
    }
    
    // 创建起点和终点标记
    const markers = [
      // 起点标记
      {
        id: 0,
        longitude: this.data.longitude,
        latitude: this.data.latitude,
        width: 32,
        height: 32,
        callout: {
          content: '当前位置',
          color: '#FFFFFF',
          bgColor: '#3A7FED',
          padding: 8,
          borderRadius: 4,
          display: 'ALWAYS'
        }
      },
      // 终点标记
      {
        id: 1,
        longitude: this.data.currentOrder.delivery_longitude,
        latitude: this.data.currentOrder.delivery_latitude,
        width: 32,
        height: 32,
        callout: {
          content: '配送地址',
          color: '#FFFFFF',
          bgColor: '#FF5151',
          padding: 8,
          borderRadius: 4,
          display: 'ALWAYS'
        }
      }
    ];
    
    // 设置路线和标记
    this.setData({
      polyline: [{
        points: points,
        color: '#3A7FED',
        width: 6,
        arrowLine: true
      }],
      markers: markers
    });
    
    // 缩放地图以包含起点和终点
    this.includePoints(points);
  },
  
  // 缩放地图以包含所有点
  includePoints(points) {
    if (!points || points.length < 2) return;
    
    console.log('缩放地图以包含所有点');
    
    try {
      const mapCtx = wx.createMapContext('deliveryMap', this);
      mapCtx.includePoints({
        points: points,
        padding: [80, 80, 80, 80]
      });
    } catch (error) {
      console.error('缩放地图失败:', error);
    }
  },
  
  // 临时解决方案：渲染简单路线
  renderSimpleRoute(route) {
    const { from, to } = route
    
    // 创建简单直线连接
    this.setData({
      polyline: [{
        points: [
          {
            longitude: from.longitude,
            latitude: from.latitude
          },
          {
            longitude: to.longitude,
            latitude: to.latitude
          }
        ],
        color: '#3A7FED',
        width: 6,
        arrowLine: true
      }],
      markers: [
        // 起点标记
        {
          id: 0,
          longitude: from.longitude,
          latitude: from.latitude,
          width: 32,
          height: 32,
          callout: {
            content: '当前位置',
            color: '#FFFFFF',
            bgColor: '#3A7FED',
            padding: 8,
            borderRadius: 4,
            display: 'ALWAYS'
          }
        },
        // 终点标记
        {
          id: 1,
          longitude: to.longitude,
          latitude: to.latitude,
          width: 32,
          height: 32,
          callout: {
            content: '配送地址',
            color: '#FFFFFF',
            bgColor: '#FF5151',
            padding: 8,
            borderRadius: 4,
            display: 'ALWAYS'
          }
        }
      ]
    })
  },
  
  // 计算两点之间的距离（米）
  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000 // 地球半径，单位米
    const dLat = this.deg2rad(lat2 - lat1)
    const dLon = this.deg2rad(lon2 - lon1)
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) * 
      Math.sin(dLon/2) * Math.sin(dLon/2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    const distance = R * c
    return distance
  },
  
  // 角度转弧度
  deg2rad(deg) {
    return deg * (Math.PI/180)
  },
  
  // 估计行驶时间（分钟）
  estimateDuration(distance) {
    // 假设平均速度为40km/h
    const averageSpeed = 40 * 1000 / 60 // 米/分钟
    return Math.round(distance / averageSpeed)
  },

  // 切换位置选择器显示
  toggleLocationPicker() {
    this.setData({
      showLocationPicker: !this.data.showLocationPicker
    });
  },

  // 选择位置类型
  selectLocation(e) {
    const locationType = e.currentTarget.dataset.type;
    this.setData({ showLocationPicker: false });
    
    // 使用配置里的地图密钥，避免在代码中硬编码
    const key = config.mapKey;
    const referer = '万邦送货'; // 调用插件的app的名称
    
    wx.navigateTo({
      url: `plugin://chooseLocation/index?key=${key}&referer=${referer}`
    });
  },

  // 联系客户
  callCustomer() {
    if (this.data.customerPhone) {
      wx.makePhoneCall({
        phoneNumber: this.data.customerPhone
      });
    } else {
      wx.showToast({
        title: '电话号码不可用',
        icon: 'none'
      });
    }
  },

  // 更新订单状态
  async updateOrderStatus() {
    if (!this.data.currentOrder) return

    try {
      // 如果当前是"完成配送"状态，完成订单
      if (this.data.nextActionText === '完成配送') {
        // 调用后端接口完成订单，使用订单号
        const res = await api.completeOrder(this.data.currentOrder.order_no);
        if (res.code !== 200) {
          wx.showToast({
            title: res.message || '完成订单失败',
            icon: 'none'
          });
          return;
        }
      }
      
      wx.showToast({
        title: '状态更新成功',
        icon: 'success'
      })
      
      // 如果当前是"接单"状态，更新为"正在前往"
      if (this.data.nextActionText === '接单') {
        this.setData({
          orderStatus: '正在前往',
          nextActionText: '完成配送'
        })
      } 
      // 如果当前是"完成配送"状态，完成订单
      else if (this.data.nextActionText === '完成配送') {
        // 完成订单后重置状态
        this.setData({
          currentOrder: null,
          deliveryStatus: '空闲',
          orderStatus: '',
          customerPhone: '',
          customerAddress: '',
          routeDistance: '0.0',
          routeTime: '0',
          nextActionText: '接单',
          markers: [],
          polyline: []
        })
        
        // 完成订单后更新司机状态为空闲 (0=空闲)
        this.updateDriverStatus(0).catch(err => {
          console.error('更新司机状态失败:', err);
        });
      }
    } catch (error) {
      wx.showToast({
        title: '状态更新失败',
        icon: 'none'
      })
    }
  },

  // 标记点击事件
  onMarkerTap(e) {
    const markerId = e.markerId
    // TODO: 处理标记点击事件
  },
  
  // 导航到目的地
  navigateToDestination() {
    if (!this.data.currentOrder) return
    
    const { delivery_address, delivery_latitude, delivery_longitude } = this.data.currentOrder
    
    // 使用微信内置地图导航
    wx.openLocation({
      latitude: delivery_latitude,
      longitude: delivery_longitude,
      name: delivery_address,
      scale: 18
    })
  },

  // 反向地址解析（根据经纬度获取地址）
  reverseGeocoder(lat, lng) {
    const app = getApp();
    
    // 检查是否允许调用地图API
    if (!app.globalData.enableMapApiCalls) {
      console.log('地图API调用已禁用，跳过反向地址解析');
      return;
    }
    
    // 检查API调用频率限制
    if (!app.canCallMapApi('reverseGeocoder')) {
      console.log('API调用过于频繁，跳过本次反向地址解析');
      return;
    }
    
    // 生成调用的唯一键
    const locationKey = `${lat.toFixed(6)},${lng.toFixed(6)}`;
    
    // 如果30分钟内已经查询过该位置，直接使用缓存结果
    const cacheTime = 30 * 60 * 1000; // 30分钟
    const now = Date.now();
    const cachedResult = this.data.lastGeocoderCalls[locationKey];
    
    if (cachedResult && (now - cachedResult.timestamp) < cacheTime) {
      console.log('使用缓存的地址解析结果');
      return;
    }
    
    // 直接调用反向地址解析接口，而不是通过SDK
    const { config } = require('../../utils/config');
    const url = `https://apis.map.qq.com/ws/geocoder/v1/?location=${lat},${lng}&key=${config.mapKey}`;
    
    wx.request({
      url: url,
      method: 'GET',
      success: (res) => {
        const data = res.data;
        if (data.status === 0) {
          // 缓存结果
          this.setData({
            [`lastGeocoderCalls.${locationKey}`]: {
              result: data.result,
              timestamp: now
            }
          });
          
          console.log('反向地址解析成功:', data.result.address);
        } else {
          console.error('反向地址解析返回错误:', data);
        }
      },
      fail: (error) => {
        console.error('反向地址解析请求错误:', error);
        
        // 显示友好的错误信息
        if (error.status === 121 || (error.data && error.data.status === 121)) {
          wx.showToast({
            title: '地图服务配额已用尽，请明天再试',
            icon: 'none',
            duration: 3000
          });
        }
      }
    });
  },
  
  // 地址搜索功能
  searchAddress(keyword) {
    if (!keyword) return;
    
    // 开发阶段，检查一下是否需要调用API以节省配额
    if (!app.globalData || !app.globalData.enableMapApiCalls) {
      console.log('地图API调用已暂时禁用，以节省配额');
      return;
    }
    
    // 直接调用地点搜索接口，而不是通过SDK
    const { config } = require('../../utils/config');
    const encodedKeyword = encodeURIComponent(keyword);
    const url = `https://apis.map.qq.com/ws/place/v1/search?keyword=${encodedKeyword}&boundary=region(全国,0)&page_size=10&key=${config.mapKey}`;
    
    wx.request({
      url: url,
      method: 'GET',
      success: (res) => {
        const data = res.data;
        if (data.status === 0) {
          console.log('地址搜索成功:', data);
          const searchResults = data.data;
          // 可以使用搜索结果更新UI
          // 这里可以显示搜索结果列表供用户选择
        } else {
          console.error('地址搜索返回错误:', data);
          wx.showToast({
            title: '搜索失败: ' + data.message,
            icon: 'none'
          });
        }
      },
      fail: (error) => {
        console.error('地址搜索请求错误:', error);
        wx.showToast({
          title: '搜索失败',
          icon: 'none'
        });
      }
    });
  },

  // 获取新订单
  getNewOrders() {
    console.log('页面调用getNewOrders开始获取可派送订单...');
    
    // 调用新的获取可派送订单接口 (status=1表示待接单状态)
    api.getAvailableOrders(1, 1, 10)
      .then(res => {
        console.log('获取可派送订单结果:', res);
        
        if (res.code === 200 && res.data && res.data.records && res.data.records.length > 0) {
          console.log('成功获取到可派送订单数据:', res.data.records);
          
          // 取第一条订单推送给司机
          const firstOrder = res.data.records[0];
          console.log('取第一条订单:', firstOrder);
          
          // 检查订单数据完整性
          if (!firstOrder.delivery_address) {
            console.error('订单缺少配送地址');
            return;
          }
          
          const orderData = {
            // 使用order_no作为唯一标识
            id: firstOrder.order_no,
            order_no: firstOrder.order_no,
            customer_phone: firstOrder.customer_phone || '',
            delivery_address: firstOrder.delivery_address,
            // 使用默认坐标（广州市中心）因为后端没有返回坐标
            delivery_latitude: 23.129163,
            delivery_longitude: 113.264435,
            status_text: '待接单',
            next_action_text: '接单',
            goods_weight: firstOrder.goods_weight,
            delivery_fee: firstOrder.delivery_fee,
            remark: firstOrder.remark
          };
          
          console.log('准备显示新订单，处理后的数据:', orderData);
          console.log('订单数据字段检查:', {
            hasOrderNo: !!orderData.order_no,
            hasCustomerPhone: !!orderData.customer_phone,
            hasDeliveryAddress: !!orderData.delivery_address,
            deliveryFee: orderData.delivery_fee
          });
          this.receiveNewOrder(orderData);
          
        } else {
          console.log('没有获取到可派送订单或订单为空');
        }
      })
      .catch(err => {
        console.error('获取可派送订单失败:', err);
        // 静默处理错误，不显示错误提示，避免频繁弹窗
        console.log('将在下次轮询时重试');
      });
  },
  
  // 使用默认位置处理新订单
  handleNewOrderWithDefaultLocation(newOrder) {
    wx.showToast({
      title: '地址解析失败，请联系管理员',
      icon: 'none',
      duration: 2000
    });
    
    // 不再使用默认坐标，而是提示失败
    wx.showModal({
      title: '地址解析失败',
      content: '无法获取配送地址的坐标信息，请联系管理员更新地址信息',
      showCancel: false
    });
    
    // 取消当前操作，不显示新订单
    this.setData({
      newOrderVisible: false,
      newOrder: null
    });
  },
}) 
