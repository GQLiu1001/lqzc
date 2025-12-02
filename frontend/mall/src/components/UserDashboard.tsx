import { useEffect, useRef, type RefObject, useState, type FormEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ArrowLeft,
  Crown,
  History,
  MapPin,
  ShieldCheck,
  Sparkles,
  Ticket,
  Wallet,
  Truck,
  Clock,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { ProfileEditDialog } from "./ProfileEditDialog";
import { mallApi, authApi, addressApi, pointsApi, couponApi, orderApi, UserProfile, Address, PointsOverview, PointsLog, MyCoupon, OrderListItem, isLoggedIn, clearCustomerToken } from "@/lib/api";
import { Edit, Gift, Volume2, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { CouponCenter } from "./CouponCenter";

type UserDashboardProps = {
  onBack?: () => void;
};

type AddressForm = {
  id?: number;
  label: string;
  name: string;
  phone: string;
  province: string;
  city: string;
  district: string;
  detail: string;
  isDefault: boolean;
};

// 积分来源类型映射
const getSourceTypeName = (sourceType: number): string => {
  const typeMap: { [key: number]: string } = {
    1: '下单赠送',
    2: '退款回退',
    3: '支付抵扣',
    4: '人工调整',
  };
  return typeMap[sourceType] || '其他';
};

const UserDashboard = ({ onBack }: UserDashboardProps) => {
  const ordersRef = useRef<HTMLDivElement | null>(null);
  const addressRef = useRef<HTMLDivElement | null>(null);

  const scrollTo = (ref: RefObject<HTMLDivElement>) => {
    const headerOffset = 96; // 顶部固定bar高度 + 间距
    const el = ref.current;
    if (el) {
      const rect = el.getBoundingClientRect();
      const target = rect.top + window.scrollY - headerOffset;
      window.scrollTo({ top: target, behavior: "smooth" });
    }
  };

  const [orderDialogOpen, setOrderDialogOpen] = useState(false);
  const [activeOrder, setActiveOrder] = useState<OrderListItem | null>(null);
  const [addressDialogOpen, setAddressDialogOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<AddressForm | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [detailDialog, setDetailDialog] = useState<"points" | "coupon" | null>(null);
  const [couponFilter, setCouponFilter] = useState<"all" | "valid" | "invalid">("all");
  const [addressFormError, setAddressFormError] = useState<string | null>(null);
  const [isAuthed, setIsAuthed] = useState(() => isLoggedIn());
  const [authTab, setAuthTab] = useState<"login" | "register" | "reset">("login");
  const [authForm, setAuthForm] = useState({
    phone: "",
    password: "",
    confirm: "",
    nickname: "",
  });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const { toast } = useToast();
  
  // 地址相关状态
  const [addresses, setAddresses] = useState<AddressForm[]>([]);
  const [addressLoading, setAddressLoading] = useState(false);
  
  // 积分相关状态
  const [pointsOverview, setPointsOverview] = useState<PointsOverview>({
    balance: 0,
    frozen: 0,
    total_earned: 0,
    total_spent: 0,
  });
  const [pointsLogs, setPointsLogs] = useState<PointsLog[]>([]);
  const [pointsLoading, setPointsLoading] = useState(false);
  
  // 优惠券相关状态
  const [myCoupons, setMyCoupons] = useState<MyCoupon[]>([]);
  const [couponsLoading, setCouponsLoading] = useState(false);
  
  // 订单相关状态
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  
  // 领券中心状态
  const [couponCenterOpen, setCouponCenterOpen] = useState(false);
  
  // 公告横幅状态
  const [showAnnouncement, setShowAnnouncement] = useState(true);

  const openAddAddress = () => {
    setEditingAddress({
      label: "家",
      name: "",
      phone: "",
      province: "",
      city: "",
      district: "",
      detail: "",
      isDefault: false,
    });
    setEditingIndex(null);
    setAddressFormError(null);
    setAddressDialogOpen(true);
  };

  const openEditAddress = (addr: AddressForm, idx: number) => {
    setEditingAddress({ 
      ...addr,
      province: addr.province || '',
      city: addr.city || '',
      district: addr.district || '',
    });
    setEditingIndex(idx);
    setAddressFormError(null);
    setAddressDialogOpen(true);
  };

  const handleAuthSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);

    try {
      if (authTab === "login") {
        // 登录
        if (!authForm.phone || !authForm.password) {
          throw new Error("请输入手机号和密码");
        }
        await authApi.login({ phone: authForm.phone, password: authForm.password });
        toast({ title: "登录成功", description: "欢迎回来！" });
        setIsAuthed(true);
      } else if (authTab === "register") {
        // 注册
        if (!authForm.phone || !authForm.password) {
          throw new Error("请输入手机号和密码");
        }
        if (authForm.password !== authForm.confirm) {
          throw new Error("两次输入的密码不一致");
        }
        await authApi.register({
          phone: authForm.phone,
          password: authForm.password,
          nickname: authForm.nickname || undefined,
          register_channel: "H5",
        });
        toast({ title: "注册成功", description: "请使用新账号登录" });
        setAuthTab("login");
        setAuthForm(prev => ({ ...prev, password: "", confirm: "" }));
      } else if (authTab === "reset") {
        // 忘记密码
        if (!authForm.phone || !authForm.password) {
          throw new Error("请输入手机号和新密码");
        }
        await authApi.forgotPassword({
          phone: authForm.phone,
          sms_code: "123456", // 简化实现，不校验短信码
          new_password: authForm.password,
        });
        toast({ title: "密码重置成功", description: "请使用新密码登录" });
        setAuthTab("login");
        setAuthForm(prev => ({ ...prev, password: "" }));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "操作失败";
      setAuthError(message);
      toast({ title: "操作失败", description: message, variant: "destructive" });
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      toast({ title: "已退出登录" });
    } catch (error) {
      console.error("登出失败:", error);
    }
    setIsAuthed(false);
    setAuthTab("login");
    setAuthForm({ phone: "", password: "", confirm: "", nickname: "" });
  };

  const saveAddress = async () => {
    if (!editingAddress) return;
    if (!editingAddress.name || !editingAddress.phone || !editingAddress.detail) {
      setAddressFormError("请填写收货人、手机号和详细地址");
      return;
    }

    try {
      // 解析地址（简单处理，假设detail格式为"省 市 区 详细地址"）
      const parts = editingAddress.detail.split(' ');
      const province = parts[0] || '';
      const city = parts[1] || '';
      const district = parts[2] || '';
      const detailAddr = parts.slice(3).join(' ') || editingAddress.detail;

      const addressData: Address = {
        receiver_name: editingAddress.name,
        receiver_phone: editingAddress.phone,
        province: province,
        city: city,
        district: district,
        detail: detailAddr,
        tag: editingAddress.label,
        is_default: editingAddress.isDefault ? 1 : 0,
      };

      if (editingAddress.id) {
        // 修改地址
        addressData.id = editingAddress.id;
        await addressApi.updateAddress(addressData);
        toast({ title: "地址修改成功" });
      } else {
        // 新增地址
        await addressApi.addAddress(addressData);
        toast({ title: "地址添加成功" });
      }

      // 重新加载地址列表
      await fetchAddresses();
      
      setAddressDialogOpen(false);
      setEditingAddress(null);
      setEditingIndex(null);
      setAddressFormError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "操作失败";
      setAddressFormError(message);
      toast({ title: "操作失败", description: message, variant: "destructive" });
    }
  };

  // 防止弹窗打开时 body 右侧出现补偿空白，并记录当前计算值便于排查
  useEffect(() => {
    if (orderDialogOpen) {
      const bodyStyle = window.getComputedStyle(document.body);
      const htmlStyle = window.getComputedStyle(document.documentElement);
      const scrollBarWidth = window.innerWidth - document.documentElement.clientWidth;
      console.log("[Dialog] body padding-right:", bodyStyle.paddingRight, "html padding-right:", htmlStyle.paddingRight, "scrollbarWidth:", scrollBarWidth);

      const prevBodyPadding = document.body.style.paddingRight;
      const prevHtmlPadding = document.documentElement.style.paddingRight;
      document.body.style.paddingRight = "0px";
      document.documentElement.style.paddingRight = "0px";

      return () => {
        document.body.style.paddingRight = prevBodyPadding;
        document.documentElement.style.paddingRight = prevHtmlPadding;
      };
    }
  }, [orderDialogOpen]);

  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile>({
    id: 0,
    nickname: "加载中...",
    phone: "",
    avatar: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200&h=200&fit=crop",
    level_name: "普通会员",
    email: ""
  });

  // 会员等级名称映射
  const getLevelName = (level?: number): string => {
    const levelMap: { [key: number]: string } = {
      1: '普通会员',
      2: '银卡会员',
      3: '金卡会员',
      4: '黑金会员',
    };
    return levelMap[level || 1] || '普通会员';
  };

  const fetchProfile = async () => {
    try {
      const profile = await authApi.getProfile();
      setUserProfile(prev => ({
        ...prev,
        ...profile,
        // 如果后端没返回头像，保留默认
        avatar: profile.avatar || prev.avatar,
        // 根据level数字转换为level_name
        level_name: profile.level_name || getLevelName(profile.level)
      }));
    } catch (error) {
      console.error("Failed to fetch profile", error);
      // 如果获取失败（可能是token过期），清除登录状态
      if (error instanceof Error && error.message.includes("登录")) {
        clearCustomerToken();
        setIsAuthed(false);
      }
    }
  };

  // 加载地址列表
  const fetchAddresses = async () => {
    try {
      setAddressLoading(true);
      const data = await addressApi.getAddressList();
      const formattedAddresses: AddressForm[] = data.map(addr => ({
        id: addr.id,
        label: addr.tag || '其他',
        name: addr.receiver_name,
        phone: addr.receiver_phone,
        province: addr.province,
        city: addr.city,
        district: addr.district,
        detail: `${addr.province} ${addr.city} ${addr.district} ${addr.detail}`,
        isDefault: addr.is_default === 1,
      }));
      setAddresses(formattedAddresses);
    } catch (error) {
      console.error("Failed to fetch addresses", error);
    } finally {
      setAddressLoading(false);
    }
  };

  // 加载积分数据
  const fetchPoints = async () => {
    try {
      setPointsLoading(true);
      const overview = await pointsApi.getOverview();
      setPointsOverview(overview);
      
      const logsData = await pointsApi.getLogs(1, 10);
      setPointsLogs(logsData.records);
    } catch (error) {
      console.error("Failed to fetch points", error);
    } finally {
      setPointsLoading(false);
    }
  };

  // 加载优惠券数据
  const fetchCoupons = async () => {
    try {
      setCouponsLoading(true);
      const data = await couponApi.getMyCoupons();
      setMyCoupons(data);
    } catch (error) {
      console.error("Failed to fetch coupons", error);
    } finally {
      setCouponsLoading(false);
    }
  };

  // 加载订单数据
  const fetchOrders = async () => {
    try {
      setOrdersLoading(true);
      const data = await orderApi.getList(undefined, 1, 10);
      setOrders(data.records);
    } catch (error) {
      console.error("Failed to fetch orders", error);
    } finally {
      setOrdersLoading(false);
    }
  };

  // 确认收货
  const handleConfirmReceive = async (orderNo: string) => {
    if (!window.confirm("确认已收到货物？确认后将获得积分奖励")) {
      return;
    }
    try {
      const result = await orderApi.confirm(orderNo);
      toast({
        title: "确认收货成功",
        description: `恭喜您获得 ${result.points_earned} 积分！`,
      });
      // 刷新数据
      fetchOrders();
      fetchPoints();
    } catch (error) {
      console.error("确认收货失败", error);
      toast({
        title: "确认收货失败",
        description: "请稍后重试",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    if (isAuthed) {
      fetchProfile();
      fetchAddresses();
      fetchPoints();
      fetchCoupons();
      fetchOrders();
    }
  }, [isAuthed]);

  // 优惠券状态判断函数
  const getCouponStatus = (coupon: MyCoupon): "active" | "warning" | "disabled" => {
    if (coupon.status === 1 || coupon.status === 2 || coupon.status === 3) {
      return "disabled";
    }
    // 检查是否即将过期（3天内）
    if (coupon.expire_time) {
      const expireDate = new Date(coupon.expire_time);
      const now = new Date();
      const diffDays = Math.ceil((expireDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      if (diffDays <= 3 && diffDays > 0) {
        return "warning";
      }
    }
    return "active";
  };

  // 优惠券类型名称
  const getCouponTypeName = (type: number): string => {
    const typeMap: { [key: number]: string } = {
      1: '满减券',
      2: '折扣券',
      3: '现金券',
    };
    return typeMap[type] || '优惠券';
  };

  // 优惠券描述
  const getCouponDesc = (coupon: MyCoupon): string => {
    if (coupon.type === 1 && coupon.threshold_amount && coupon.discount_amount) {
      return `满${coupon.threshold_amount}减${coupon.discount_amount}`;
    }
    if (coupon.type === 2 && coupon.discount_rate) {
      return `${(coupon.discount_rate * 10).toFixed(1)}折优惠`;
    }
    if (coupon.type === 3 && coupon.discount_amount) {
      return `立减${coupon.discount_amount}元`;
    }
    return '优惠券';
  };

  // 转换为展示用的优惠券格式
  const coupons = myCoupons.map(c => ({
    title: c.title,
    tag: getCouponTypeName(c.type),
    desc: getCouponDesc(c),
    expire: c.expire_time ? c.expire_time.split('T')[0] + ' 到期' : '长期有效',
    status: getCouponStatus(c),
  }));

  // 会员等级按累计获取积分计算，消费不降级
  const totalEarnedPoints = pointsOverview.total_earned;
  const currentBalance = pointsOverview.balance;
  const memberLevels = [
    { name: "普通", threshold: 0 },
    { name: "银卡", threshold: 1500 },
    { name: "金卡", threshold: 3000 },
    { name: "黑金", threshold: 6000 },
  ];

  // 订单状态名称映射
  const getOrderStatusName = (status: number): string => {
    const statusMap: { [key: number]: string } = {
      0: '待支付',
      1: '待发货',
      2: '配送中',
      3: '待确认',  // 司机已送达，等待用户确认收货
      4: '已完成',
      5: '已取消',
    };
    return statusMap[status] || '未知';
  };

  // 统计卡片数据（需要在addresses, pointsOverview, coupons之后定义）
  const stats = [
    {
      title: "积分",
      value: pointsOverview.balance.toLocaleString(),
      hint: `累计获取 ${pointsOverview.total_earned.toLocaleString()}`,
      icon: Sparkles,
      gradient: "from-indigo-500/80 to-sky-500/80",
    },
    {
      title: "优惠券",
      value: `${coupons.length} 张`,
      hint: "查看优惠券详情",
      icon: Ticket,
      gradient: "from-amber-500/80 to-orange-400/80",
    },
    {
      title: "收货地址",
      value: `${addresses.length} 个`,
      hint: "管理收货地址",
      icon: MapPin,
      gradient: "from-blue-500/80 to-purple-500/80",
    },
  ];

  if (!isAuthed) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 flex items-center justify-center px-4">
        <Card className="w-full max-w-lg border-0 shadow-2xl">
          <CardHeader className="flex-row items-center justify-between gap-4">
            <div>
              <CardTitle className="text-gray-900">账户中心</CardTitle>
              <CardDescription>登录 / 注册 / 找回密码</CardDescription>
            </div>
            <div className="flex gap-2">
              {[
                { key: "login", label: "登录" },
                { key: "register", label: "注册" },
                { key: "reset", label: "忘记密码" },
              ].map((tab) => (
                <Button
                  key={tab.key}
                  size="sm"
                  variant={authTab === tab.key ? "default" : "outline"}
                  onClick={() => setAuthTab(tab.key as "login" | "register" | "reset")}
                >
                  {tab.label}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={handleAuthSubmit}>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">手机号</p>
                <Input
                  value={authForm.phone}
                  onChange={(e) => setAuthForm((p) => ({ ...p, phone: e.target.value }))}
                  placeholder="请输入手机号"
                />
              </div>
              {authTab === "register" && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">昵称（可选）</p>
                  <Input
                    value={authForm.nickname}
                    onChange={(e) => setAuthForm((p) => ({ ...p, nickname: e.target.value }))}
                    placeholder="请输入昵称"
                  />
                </div>
              )}
              <div className="space-y-2">
                <p className="text-sm text-gray-600">{authTab === "reset" ? "新密码" : "密码"}</p>
                <Input
                  type="password"
                  value={authForm.password}
                  onChange={(e) => setAuthForm((p) => ({ ...p, password: e.target.value }))}
                  placeholder={authTab === "reset" ? "请输入新密码" : "请输入密码"}
                />
              </div>
              {authTab === "register" && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">确认密码</p>
                  <Input
                    type="password"
                    value={authForm.confirm}
                    onChange={(e) => setAuthForm((p) => ({ ...p, confirm: e.target.value }))}
                    placeholder="请再次输入密码"
                  />
                </div>
              )}
              {authError && (
                <p className="text-sm text-rose-500">{authError}</p>
              )}
              <div className="flex gap-3">
                <Button 
                  type="submit" 
                  className="bg-indigo-600 hover:bg-indigo-700 text-white flex-1"
                  disabled={authLoading}
                >
                  {authLoading ? "处理中..." : (
                    authTab === "login" ? "登录" :
                    authTab === "register" ? "注册" : "重置密码"
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setAuthForm({ phone: "", password: "", confirm: "", nickname: "" });
                    setAuthError(null);
                  }}
                >
                  清空
                </Button>
              </div>
              <p className="text-xs text-gray-500">测试提示：先注册账号，再登录</p>
            </form>
          </CardContent>
          <div className="flex items-center justify-between px-6 pb-6">
            {onBack ? (
              <Button variant="outline" onClick={onBack}>
                返回商城
              </Button>
            ) : (
              <span />
            )}
            <span className="text-xs text-gray-400">安全提示：请勿泄露账号密码</span>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <section className="container mx-auto px-4 pt-28 pb-16">
      <div className="grid gap-6">
        <Card className="border-0 bg-gradient-to-r from-sky-100 via-white to-indigo-100 shadow-xl">
          <CardHeader className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16 ring-4 ring-white/70 shadow-lg">
                <AvatarImage src={userProfile.avatar} alt={userProfile.nickname} />
                <AvatarFallback>CC</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm text-gray-500">欢迎回来</p>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-2xl font-bold text-gray-900">
                    {userProfile.nickname}
                  </span>
                  <Badge className="bg-indigo-600 text-white shadow-sm cursor-pointer" onClick={() => setDetailDialog("points")}>
                    <Crown className="h-3 w-3 mr-1" />
                    {userProfile.level_name || "普通会员"}
                  </Badge>
                  <Button variant="ghost" size="icon" className="h-6 w-6 ml-1" onClick={() => setProfileDialogOpen(true)}>
                    <Edit className="h-4 w-4 text-gray-500" />
                  </Button>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {userProfile.phone} · {userProfile.email || "未绑定邮箱"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                onClick={() => scrollTo(ordersRef)}
              >
                <History className="h-4 w-4 mr-1.5" />
                跳到历史订单
              </Button>
              <Button
                variant="outline"
                className="border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                onClick={() => scrollTo(addressRef)}
              >
                <MapPin className="h-4 w-4 mr-1.5" />
                跳到收货地址
              </Button>
              {onBack && (
                <Button
                  variant="outline"
                  className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                  onClick={onBack}
                >
                  <ArrowLeft className="h-4 w-4 mr-1.5" />
                  返回商城
                </Button>
              )}
              <Button
                variant="outline"
                className="border-rose-200 text-rose-600 hover:bg-rose-50"
                onClick={handleLogout}
              >
                退出登录
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* 活动公告横幅 */}
        {showAnnouncement && (
          <Card className="border-0 bg-gradient-to-r from-rose-500 via-orange-500 to-amber-500 text-white shadow-lg overflow-hidden">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <Volume2 className="h-5 w-5 shrink-0 animate-pulse" />
                  <span className="font-medium">🎉 限时抢券：新用户专享优惠券限量发放中，先到先得！</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    size="sm"
                    variant="secondary"
                    className="bg-white/20 hover:bg-white/30 text-white border-white/30 h-7"
                    onClick={() => setCouponCenterOpen(true)}
                  >
                    <Gift className="h-3 w-3 mr-1" />
                    立即领取
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-white/80 hover:text-white hover:bg-white/20"
                    onClick={() => setShowAnnouncement(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid md:grid-cols-4 gap-4">
          {stats.map((item) => (
            <Card
              key={item.title}
              className={`border-0 bg-gradient-to-br ${item.gradient} text-white shadow-lg`}
            >
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-white/80">{item.title}</p>
                  <item.icon className="h-5 w-5" />
                </div>
                <p className="text-3xl font-bold mt-2">{item.value}</p>
                <p className="text-xs text-white/80 mt-1">{item.hint}</p>
              </CardContent>
            </Card>
          ))}
          
          {/* 领券中心入口 */}
          <Card
            className="border-0 bg-gradient-to-br from-rose-500/80 to-pink-500/80 text-white shadow-lg cursor-pointer hover:scale-105 transition-transform"
            onClick={() => setCouponCenterOpen(true)}
          >
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm text-white/80">领券中心</p>
                <Gift className="h-5 w-5" />
              </div>
              <p className="text-3xl font-bold mt-2">抢券</p>
              <p className="text-xs text-white/80 mt-1">限时优惠，先到先得</p>
            </CardContent>
          </Card>
        </div>


        <div className="grid lg:grid-cols-2 gap-6">
          <Card className="border-0 bg-white/90 backdrop-blur shadow-xl">
            <CardHeader className="flex-row items-start justify-between gap-2">
              <div>
                <CardTitle className="flex items-center gap-2 text-gray-900">
                  <Sparkles className="h-5 w-5 text-indigo-500" />
                  积分
                </CardTitle>
                <CardDescription>消费可获得积分并抵扣现金</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setDetailDialog("points")}>
                查看详情
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">当前积分</p>
                    <p className="text-3xl font-bold text-indigo-700">{pointsOverview.balance.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">可抵扣</p>
                    <p className="text-xl font-semibold text-indigo-700">¥{(pointsOverview.balance / 10).toFixed(0)}</p>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>累计获取 · {pointsOverview.total_earned.toLocaleString()}</span>
                    <span>累计消耗 {pointsOverview.total_spent.toLocaleString()}</span>
                  </div>
                  <Progress value={pointsOverview.total_earned > 0 ? (pointsOverview.balance / pointsOverview.total_earned) * 100 : 0} />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>最近变动</span>
                  <span>{pointsLogs.length > 0 ? `共 ${pointsLogs.length} 条记录` : '暂无记录'}</span>
                </div>
                <div className="grid gap-2">
                  {pointsLogs.slice(0, 2).map((log) => (
                    <div key={log.id} className="flex items-center justify-between rounded-xl border border-gray-100 px-4 py-2.5">
                      <div className="flex items-center gap-3">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-semibold text-sm ${
                          log.change_amount >= 0 
                            ? 'bg-indigo-100 text-indigo-700' 
                            : 'bg-pink-100 text-pink-700'
                        }`}>
                          {log.change_amount >= 0 ? `+${log.change_amount}` : log.change_amount}
                        </div>
                        <div>
                          <p className="font-medium text-gray-800">{log.remark || getSourceTypeName(log.source_type)}</p>
                          <p className="text-xs text-gray-500">余额：{log.balance_after}</p>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">{log.create_time?.split(' ')[0]}</span>
                    </div>
                  ))}
                  {pointsLogs.length === 0 && (
                    <div className="text-center text-gray-400 py-4 text-sm">暂无积分变动记录</div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 bg-white/90 backdrop-blur shadow-xl">
            <CardHeader className="flex-row items-start justify-between gap-2">
              <div>
                <CardTitle className="flex items-center gap-2 text-gray-900">
                  <Ticket className="h-5 w-5 text-amber-500" />
                  优惠券
                </CardTitle>
                <CardDescription>精选券包，实时展示即将到期的福利</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setDetailDialog("coupon")}>
                查看详情
              </Button>
            </CardHeader>
            <CardContent className="grid gap-3">
              {coupons.map((coupon) => (
                <div
                  key={coupon.title}
                  className={`rounded-2xl border p-4 space-y-2 transition-all hover:-translate-y-1 hover:shadow ${coupon.status === "warning"
                      ? "border-amber-200 bg-amber-50/60"
                      : coupon.status === "disabled"
                        ? "border-gray-200 bg-gray-50"
                        : "border-emerald-100 bg-emerald-50/70"
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-xl font-semibold text-gray-900">
                      {coupon.title}
                    </div>
                    <Badge
                      variant="outline"
                      className="border-dashed border-gray-300 bg-white/60 text-gray-700"
                    >
                      {coupon.tag}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">{coupon.desc}</p>
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-xs ${coupon.status === "warning"
                          ? "text-amber-700"
                          : "text-gray-500"
                        }`}
                    >
                      {coupon.expire}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-indigo-700 hover:text-indigo-900"
                    >
                      立即使用
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div ref={ordersRef} className="lg:col-span-2">
            <Card className="border-0 bg-white/90 backdrop-blur shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900">
                  <History className="h-5 w-5 text-teal-500" />
                  历史订单
                </CardTitle>
                <CardDescription>订单流转、售后状态一目了然</CardDescription>
              </CardHeader>
              <CardContent className="px-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="pl-6">订单号</TableHead>
                      <TableHead>金额</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>时间</TableHead>
                      <TableHead className="pr-6 text-right">备注</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                          暂无订单记录
                        </TableCell>
                      </TableRow>
                    ) : (
                      orders.map((order) => (
                        <TableRow
                          key={order.order_no}
                          className="hover:bg-gray-50/70 cursor-pointer"
                          onClick={() => {
                            setActiveOrder(order);
                            setOrderDialogOpen(true);
                          }}
                        >
                          <TableCell className="pl-6 font-medium text-gray-900">
                            {order.order_no}
                          </TableCell>
                          <TableCell className="text-gray-900 font-semibold">
                            ¥{order.payable_amount?.toFixed(2) || '0.00'}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={`${
                                order.status === 4 ? 'bg-teal-50 border-teal-200 text-teal-700' :
                                order.status === 3 ? 'bg-blue-50 border-blue-200 text-blue-700' :
                                order.status === 5 ? 'bg-gray-100 border-gray-200 text-gray-500' :
                                'bg-amber-50 border-amber-200 text-amber-700'
                              }`}
                            >
                              {getOrderStatusName(order.status)}
                            </Badge>
                            {order.status === 3 && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="ml-2 text-xs h-6 border-green-500 text-green-600 hover:bg-green-50"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleConfirmReceive(order.order_no);
                                }}
                              >
                                确认收货
                              </Button>
                            )}
                          </TableCell>
                          <TableCell className="text-gray-500">{order.create_time?.split(' ')[0] || '-'}</TableCell>
                          <TableCell className="pr-6 text-right text-gray-500">
                            {order.items?.length || 0} 件商品
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          <div ref={addressRef}>
            <Card className="border-0 bg-white/90 backdrop-blur shadow-xl">
              <CardHeader className="flex-row items-start justify-between gap-2">
                <div>
                  <CardTitle className="flex items-center gap-2 text-gray-900">
                    <MapPin className="h-5 w-5 text-rose-500" />
                    收货地址
                  </CardTitle>
                  <CardDescription>常用地址，支持工地/公司/家庭快速切换</CardDescription>
                </div>
                <Button size="sm" onClick={openAddAddress}>
                  添加
                </Button>
              </CardHeader>
              <CardContent className="grid md:grid-cols-1 gap-4">
                {addresses.map((address, idx) => (
                  <div
                    key={`${address.detail}-${idx}`}
                    className="rounded-2xl border border-gray-100 p-4 space-y-3 bg-gradient-to-br from-gray-50 via-white to-gray-50 hover:shadow"
                  >
                    <div className="flex items-center justify-between">
                      <Badge
                        variant="outline"
                        className="bg-white text-gray-700 border-gray-200"
                      >
                        {address.label}
                      </Badge>
                      {address.isDefault && (
                        <Badge className="bg-emerald-100 text-emerald-700 border-none">
                          默认
                        </Badge>
                      )}
                    </div>
                    <div className="space-y-1">
                      <p className="text-gray-900 font-semibold">{address.name}</p>
                      <p className="text-sm text-gray-600">{address.phone}</p>
                      <p className="text-sm text-gray-700">{address.detail}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-indigo-700 hover:text-indigo-900"
                      onClick={() => openEditAddress(address, idx)}
                    >
                      修改
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Dialog open={detailDialog === "points"} onOpenChange={(open) => setDetailDialog(open ? "points" : null)} modal={false}>
        <DialogContent className="sm:max-w-lg bg-white/95 backdrop-blur">
          <DialogHeader>
            <DialogTitle>积分详情</DialogTitle>
            <DialogDescription>SQL 日志表：loyalty_points_account / loyalty_points_log</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/80 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">当前积分</p>
                  <p className="text-2xl font-bold text-indigo-700">{currentBalance.toLocaleString()}</p>
                </div>
                <div className="text-right text-sm text-gray-600">
                  下一级：{
                    memberLevels.find((l) => totalEarnedPoints < l.threshold)?.name ?? "已是最高等级"
                  }
                </div>
              </div>
              <div className="mt-3 space-y-2">
                {memberLevels.map((level, idx) => {
                  // 会员等级按累计获取积分判断
                  const progress = level.threshold === 0 ? 100 : Math.min(100, (totalEarnedPoints / level.threshold) * 100);
                  const isCurrentLevel =
                    idx === memberLevels.length - 1
                      ? totalEarnedPoints >= level.threshold
                      : totalEarnedPoints >= level.threshold && totalEarnedPoints < memberLevels[idx + 1].threshold;
                  const nextThreshold = memberLevels[idx + 1]?.threshold;
                  const gap =
                    nextThreshold && totalEarnedPoints < nextThreshold ? nextThreshold - totalEarnedPoints : 0;
                  return (
                    <div key={level.name} className="rounded-xl bg-white/70 border border-indigo-100 p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={isCurrentLevel ? "default" : "outline"}
                            className={isCurrentLevel ? "bg-indigo-600 text-white" : "border-indigo-200 text-indigo-700"}
                          >
                            {level.name}
                          </Badge>
                          <span className="text-xs text-gray-500">达标 {level.threshold} 分</span>
                        </div>
                        {gap > 0 && isCurrentLevel && (
                          <span className="text-xs text-amber-600">还差 {gap} 分升至 {memberLevels[idx + 1].name}</span>
                        )}
                        {idx === memberLevels.length - 1 && isCurrentLevel && (
                          <span className="text-xs text-emerald-600">已是最高等级</span>
                        )}
                      </div>
                      <Progress value={progress} />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          <div className="space-y-3">
            {pointsLogs.length === 0 ? (
              <div className="text-center text-gray-500 py-4">暂无积分记录</div>
            ) : (
              pointsLogs.map((log) => (
                <div key={log.id} className="rounded-xl border border-gray-100 px-4 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{log.remark || getSourceTypeName(log.source_type)}</p>
                    <p className="text-xs text-gray-500">变动后余额：{log.balance_after}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-bold ${log.change_amount >= 0 ? "text-emerald-600" : "text-rose-500"}`}>
                      {log.change_amount >= 0 ? `+${log.change_amount}` : log.change_amount}
                    </p>
                    <p className="text-xs text-gray-500">{log.create_time?.split('T')[0]}</p>
                  </div>
                </div>
              ))
            )}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDetailDialog(null)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={detailDialog === "coupon"} onOpenChange={(open) => setDetailDialog(open ? "coupon" : null)} modal={false}>
        <DialogContent className="sm:max-w-lg bg-white/95 backdrop-blur">
          <DialogHeader>
            <DialogTitle>优惠券详情</DialogTitle>
            <DialogDescription>SQL 日志表：coupon_template / customer_coupon</DialogDescription>
          </DialogHeader>
          <div className="flex gap-2 mb-3">
            {[
              { key: "all", label: "全部" },
              { key: "valid", label: "有效" },
              { key: "invalid", label: "失效" },
            ].map((tab) => (
              <Button
                key={tab.key}
                variant={couponFilter === tab.key ? "default" : "outline"}
                size="sm"
                onClick={() => setCouponFilter(tab.key as "all" | "valid" | "invalid")}
              >
                {tab.label}
              </Button>
            ))}
          </div>
          <div className="space-y-3">
            {coupons
              .filter((coupon) => {
                if (couponFilter === "all") return true;
                if (couponFilter === "valid") return coupon.status !== "disabled";
                return coupon.status === "disabled";
              })
              .map((coupon) => (
                <div key={`log-${coupon.title}`} className="rounded-xl border border-gray-100 px-4 py-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-900">{coupon.title}</p>
                    <Badge variant="outline" className="border-dashed border-gray-300 bg-white/60 text-gray-700">
                      {coupon.tag}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{coupon.desc}</p>
                  <p className="text-xs text-gray-400">有效期：{coupon.expire}</p>
                </div>
              ))}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDetailDialog(null)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>


      <Dialog open={addressDialogOpen} onOpenChange={setAddressDialogOpen} modal={false}>
        <DialogContent className="sm:max-w-lg bg-white/95 backdrop-blur">
          <DialogHeader>
            <DialogTitle>{editingIndex === null ? "添加地址" : "修改地址"}</DialogTitle>
            <DialogDescription>收货地址表：customer_address</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-gray-500 mb-1">标签（家/公司/工地）</p>
                <Input
                  value={editingAddress?.label ?? ""}
                  onChange={(e) => setEditingAddress((prev) => prev ? { ...prev, label: e.target.value } : prev)}
                  placeholder="家"
                />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">收货人</p>
                <Input
                  value={editingAddress?.name ?? ""}
                  onChange={(e) => setEditingAddress((prev) => prev ? { ...prev, name: e.target.value } : prev)}
                  placeholder="姓名"
                />
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">手机号</p>
              <Input
                value={editingAddress?.phone ?? ""}
                onChange={(e) => setEditingAddress((prev) => prev ? { ...prev, phone: e.target.value } : prev)}
                placeholder="13800000000"
              />
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">详细地址</p>
              <Input
                value={editingAddress?.detail ?? ""}
                onChange={(e) => setEditingAddress((prev) => prev ? { ...prev, detail: e.target.value } : prev)}
                placeholder="省市区 + 详细街道门牌号"
              />
            </div>
            <div className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2">
              <span className="text-sm text-gray-700">设为默认地址</span>
              <Switch
                checked={editingAddress?.isDefault ?? false}
                onCheckedChange={(checked) =>
                  setEditingAddress((prev) => prev ? { ...prev, isDefault: checked } : prev)
                }
              />
            </div>
            {addressFormError && <p className="text-xs text-rose-500">{addressFormError}</p>}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddressDialogOpen(false)}>取消</Button>
            <Button onClick={saveAddress}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {orderDialogOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setOrderDialogOpen(false)}
        />
      )}

      <Dialog open={orderDialogOpen} onOpenChange={setOrderDialogOpen} modal={false}>
        <DialogContent className="sm:max-w-3xl bg-white/95 backdrop-blur">
          <DialogHeader className="space-y-2">
            <div className="flex items-center justify-between">
              <DialogTitle>订单详情</DialogTitle>
            </div>
            <div className="flex items-center justify-between gap-3">
              <DialogDescription className="text-gray-500">
                {activeOrder ? `${activeOrder.order_no} · ${activeOrder.create_time}` : ""}
              </DialogDescription>
              {activeOrder ? (
                <Badge variant="outline" className={`${
                  activeOrder.status === 3 ? 'text-teal-700 border-teal-200 bg-teal-50' :
                  activeOrder.status === 4 || activeOrder.status === 5 ? 'text-gray-500 border-gray-200 bg-gray-50' :
                  'text-amber-700 border-amber-200 bg-amber-50'
                }`}>
                  {getOrderStatusName(activeOrder.status)}
                </Badge>
              ) : null}
            </div>
          </DialogHeader>

          {activeOrder && (
            <div className="space-y-6">
              <Card className="border border-gray-100">
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">订单金额</span>
                    <span className="text-xl font-bold text-gray-900">¥{activeOrder.payable_amount?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">订单状态</span>
                    <span className="text-sm text-gray-700">{getOrderStatusName(activeOrder.status)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">下单时间</span>
                    <span className="text-sm text-gray-700">{activeOrder.create_time || '-'}</span>
                  </div>
                </CardContent>
              </Card>

              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Truck className="h-4 w-4 text-indigo-500" />
                  商品明细
                </h4>
                <div className="space-y-2">
                  {activeOrder.items?.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3 rounded-xl border border-gray-100 p-3">
                      {item.picture && (
                        <img src={item.picture} alt={item.model} className="w-12 h-12 rounded object-cover" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{item.model}</p>
                        <p className="text-xs text-gray-500">数量: {item.amount}</p>
                      </div>
                    </div>
                  ))}
                  {(!activeOrder.items || activeOrder.items.length === 0) && (
                    <p className="text-sm text-gray-500 text-center py-4">暂无商品信息</p>
                  )}
                </div>
              </div>

            </div>
          )}

          <DialogFooter className="mt-4">
            <Button variant="ghost" onClick={() => setOrderDialogOpen(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <ProfileEditDialog
        open={profileDialogOpen}
        onOpenChange={setProfileDialogOpen}
        currentUser={userProfile}
        onSuccess={fetchProfile}
      />
      
      <CouponCenter
        isOpen={couponCenterOpen}
        onClose={() => setCouponCenterOpen(false)}
      />
    </section>
  );
};

export default UserDashboard;
