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

type UserDashboardProps = {
  onBack?: () => void;
};

type AddressForm = {
  label: string;
  name: string;
  phone: string;
  detail: string;
  isDefault: boolean;
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
  const [activeOrder, setActiveOrder] = useState<(typeof orders)[number] | null>(null);
  const [addressDialogOpen, setAddressDialogOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<AddressForm | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [detailDialog, setDetailDialog] = useState<"points" | "coupon" | null>(null);
  const [couponFilter, setCouponFilter] = useState<"all" | "valid" | "invalid">("all");
  const [addressFormError, setAddressFormError] = useState<string | null>(null);
  const [isAuthed, setIsAuthed] = useState(false);
  const [authTab, setAuthTab] = useState<"login" | "register" | "reset">("login");
  const [authForm, setAuthForm] = useState({
    phone: "13800138001",
    password: "123456",
    confirm: "123456",
  });

  const openAddAddress = () => {
    setEditingAddress({
      label: "家",
      name: "",
      phone: "",
      detail: "",
      isDefault: false,
    });
    setEditingIndex(null);
    setAddressFormError(null);
    setAddressDialogOpen(true);
  };

  const openEditAddress = (addr: AddressForm, idx: number) => {
    setEditingAddress({ ...addr });
    setEditingIndex(idx);
    setAddressFormError(null);
    setAddressDialogOpen(true);
  };

  const handleAuthSubmit = (e: FormEvent) => {
    e.preventDefault();
    console.log("[Auth Submit]", authTab, authForm);
    setIsAuthed(true); // mock 登录成功后进入用户中心
  };

  const handleLogout = () => {
    setIsAuthed(false);
    setAuthTab("login");
    setAuthForm({ phone: "13800138001", password: "123456", confirm: "123456" });
  };

  const saveAddress = () => {
    if (!editingAddress) return;
    if (!editingAddress.name || !editingAddress.phone || !editingAddress.detail) {
      setAddressFormError("请填写收货人、手机号和详细地址");
      return;
    }

    setAddresses((prev) => {
      const next = [...prev];
      if (editingAddress.isDefault) {
        next.forEach((item) => (item.isDefault = false));
      }
      if (editingIndex === null) {
        next.push(editingAddress);
      } else {
        next[editingIndex] = editingAddress;
      }
      return next;
    });

    setAddressDialogOpen(false);
    setEditingAddress(null);
    setEditingIndex(null);
    setAddressFormError(null);
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

  const userProfile = {
    name: "陈晨",
    level: "金卡会员",
    phone: "138****8001",
    email: "chenchen@example.com",
    avatar:
      "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200&h=200&fit=crop",
  };
  const currentPoints = 3000;
  const memberLevels = [
    { name: "普通", threshold: 0 },
    { name: "银卡", threshold: 1500 },
    { name: "金卡", threshold: 3000 },
    { name: "黑金", threshold: 6000 },
  ];

  const stats = [
    {
      title: "积分",
      value: "3,000",
      hint: "本月新增 +320",
      icon: Sparkles,
      gradient: "from-indigo-500/80 to-sky-500/80",
    },
    {
      title: "优惠券",
      value: "3 张",
      hint: "2 张即将到期",
      icon: Ticket,
      gradient: "from-amber-500/80 to-orange-400/80",
    },
    {
      title: "历史订单",
      value: "26",
      hint: "本月 4 笔",
      icon: History,
      gradient: "from-blue-500/80 to-purple-500/80",
    },
  ];

  const coupons = [
    {
      title: "满299减30",
      tag: "全场通用",
      desc: "下单立减，装修补贴券",
      expire: "2025-12-30 到期",
      status: "active",
    },
    {
      title: "9 折会员券",
      tag: "大件适用",
      desc: "最高减 150 元",
      expire: "即将到期：还剩 3 天",
      status: "warning",
    },
    {
      title: "新人现金券 5 元",
      tag: "新人礼",
      desc: "无门槛，胶水/辅料可用",
      expire: "2025-12-01 到期",
      status: "disabled",
    },
  ];

  const [addresses, setAddresses] = useState<AddressForm[]>([
    {
      label: "公司",
      name: "陈晨",
      phone: "138****8001",
      detail: "广东省 深圳市 南山区 科技园1号创新大厦",
      isDefault: true,
    },
    {
      label: "家",
      name: "陈晨",
      phone: "138****8001",
      detail: "广东省 深圳市 龙华区 清祥路 远景中心A座",
      isDefault: false,
    },
    {
      label: "工地",
      name: "陈晨",
      phone: "138****8001",
      detail: "广东省 佛山市 禅城区 季华六路88号",
      isDefault: false,
    },
  ]);

  const pointsLogs = [
    { amount: "+500", reason: "订单完成奖励", order: "ORD202310270001", time: "2024-10-27 16:20" },
    { amount: "-200", reason: "支付抵扣", order: "ORD202310270001", time: "2024-10-27 09:30" },
    { amount: "+150", reason: "退款回退", order: "-", time: "2024-10-18 08:00" },
  ];

  const orders = [
    {
      orderNo: "ORD202310270001",
      amount: "¥3,400.00",
      status: "已完成",
      statusCode: 3,
      tag: "包含优惠券抵扣",
      time: "2024-10-27 16:20",
      dispatch: "已完成配送",
      payChannel: "微信支付",
      address: "广东省 深圳市 南山区 科技园1号创新大厦",
      driver: {
        name: "李师傅",
        phone: "13800001111",
        avatar: "https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=200&h=200&fit=crop",
        status: "空闲",
      },
      items: [
        { name: "A8001 抛光地砖 800x800mm", qty: "100片", price: "¥2,550.00" },
        { name: "B6002 哑光墙砖 600x600mm", qty: "50片", price: "¥900.00" },
      ],
      steps: [
        { title: "待支付", time: "2024-10-27 09:20", state: "done" },
        { title: "待发货", time: "2024-10-27 10:05", state: "done" },
        { title: "待收货", time: "2024-10-27 14:00", state: "done" },
        { title: "已完成", time: "2024-10-27 16:20", state: "done" },
      ],
    },
    {
      orderNo: "ORD202310270002",
      amount: "¥1,760.00",
      status: "待发货",
      statusCode: 1,
      tag: "加急配送",
      time: "2024-10-27 11:05",
      dispatch: "待派送",
      payChannel: "支付宝",
      address: "广东省 广州市 天河区 珠江新城2号",
      driver: {
        name: "周师傅",
        phone: "13900002222",
        avatar: "https://images.unsplash.com/photo-1502685104226-ee32379fefbe?w=200&h=200&fit=crop",
        status: "忙碌",
      },
      items: [
        { name: "C9003 岩板 900x900mm", qty: "20片", price: "¥1,760.00" },
      ],
      steps: [
        { title: "待支付", time: "2024-10-27 08:35", state: "done" },
        { title: "待发货", time: "2024-10-27 11:05", state: "current" },
        { title: "待收货", time: "", state: "pending" },
        { title: "已完成", time: "", state: "pending" },
      ],
    },
    {
      orderNo: "ORD202310180066",
      amount: "¥980.00",
      status: "售后处理中",
      statusCode: 4,
      tag: "申请退款",
      time: "2024-10-18 14:33",
      dispatch: "售后处理中",
      payChannel: "微信支付",
      address: "广东省 佛山市 禅城区 季华六路88号",
      driver: {
        name: "未派单",
        phone: "-",
        avatar: "",
        status: "未分配",
      },
      items: [
        { name: "W3001 釉面墙砖 300x600mm", qty: "60片", price: "¥980.00" },
      ],
      steps: [
        { title: "待支付", time: "2024-10-18 09:10", state: "done" },
        { title: "待发货", time: "2024-10-18 10:00", state: "done" },
        { title: "售后处理中", time: "2024-10-19 13:20", state: "current" },
        { title: "已完成/关闭", time: "", state: "pending" },
      ],
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
              {authTab !== "reset" && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">密码</p>
                  <Input
                    type="password"
                    value={authForm.password}
                    onChange={(e) => setAuthForm((p) => ({ ...p, password: e.target.value }))}
                    placeholder="请输入密码"
                  />
                </div>
              )}
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
              <div className="flex gap-3">
                <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white flex-1">
                  {authTab === "login" && "登录"}
                  {authTab === "register" && "注册"}
                  {authTab === "reset" && "重置密码"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAuthForm({ phone: "", password: "", confirm: "" })}
                >
                  清空
                </Button>
              </div>
              <p className="text-xs text-gray-500">示例账号：13800138001 / 123456（免验证码）</p>
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
                <AvatarImage src={userProfile.avatar} alt={userProfile.name} />
                <AvatarFallback>CC</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm text-gray-500">欢迎回来</p>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-2xl font-bold text-gray-900">
                    {userProfile.name}
                  </span>
                  <Badge className="bg-indigo-600 text-white shadow-sm cursor-pointer" onClick={() => setDetailDialog("points")}>
                    <Crown className="h-3 w-3 mr-1" />
                    {userProfile.level}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {userProfile.phone} · {userProfile.email}
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
                    <p className="text-3xl font-bold text-indigo-700">3,000</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">可抵扣</p>
                    <p className="text-xl font-semibold text-indigo-700">¥300</p>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>本月目标 · 3,500</span>
                    <span>完成 68%</span>
                  </div>
                  <Progress value={68} />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>最新获取</span>
                  <span>更新时间：今日 09:32</span>
                </div>
                <div className="grid gap-2">
                  <div className="flex items-center justify-between rounded-xl border border-gray-100 px-4 py-2.5">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-semibold">
                        +500
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">订单完成奖励</p>
                        <p className="text-xs text-gray-500">ORD202310270001</p>
                      </div>
                    </div>
                    <span className="text-sm text-gray-500">2024-10-27</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-gray-100 px-4 py-2.5">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-xl bg-pink-100 text-pink-700 flex items-center justify-center font-semibold">
                        -200
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">支付抵扣</p>
                        <p className="text-xs text-gray-500">订单积分抵现</p>
                      </div>
                    </div>
                    <span className="text-sm text-gray-500">2024-10-27</span>
                  </div>
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
                  className={`rounded-2xl border p-4 space-y-2 transition-all hover:-translate-y-1 hover:shadow ${
                    coupon.status === "warning"
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
                      className={`text-xs ${
                        coupon.status === "warning"
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
                    {orders.map((order) => (
                      <TableRow
                        key={order.orderNo}
                        className="hover:bg-gray-50/70 cursor-pointer"
                        onClick={() => {
                          setActiveOrder(order);
                          setOrderDialogOpen(true);
                        }}
                      >
                        <TableCell className="pl-6 font-medium text-gray-900">
                          {order.orderNo}
                        </TableCell>
                        <TableCell className="text-gray-900 font-semibold">
                          {order.amount}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className="bg-teal-50 border-teal-200 text-teal-700"
                          >
                            {order.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-500">{order.time}</TableCell>
                        <TableCell className="pr-6 text-right text-gray-500">
                          {order.tag}
                        </TableCell>
                      </TableRow>
                    ))}
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
                  <p className="text-2xl font-bold text-indigo-700">{currentPoints.toLocaleString()}</p>
                </div>
                <div className="text-right text-sm text-gray-600">
                  下一级：{
                    memberLevels.find((l) => currentPoints < l.threshold)?.name ?? "已是最高等级"
                  }
                </div>
              </div>
              <div className="mt-3 space-y-2">
                {memberLevels.map((level, idx) => {
                  const progress = level.threshold === 0 ? 100 : Math.min(100, (currentPoints / level.threshold) * 100);
                  const isCurrentLevel =
                    idx === memberLevels.length - 1
                      ? currentPoints >= level.threshold
                      : currentPoints >= level.threshold && currentPoints < memberLevels[idx + 1].threshold;
                  const nextThreshold = memberLevels[idx + 1]?.threshold;
                  const gap =
                    nextThreshold && currentPoints < nextThreshold ? nextThreshold - currentPoints : 0;
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
            {pointsLogs.map((log) => (
              <div key={`${log.reason}-${log.time}`} className="rounded-xl border border-gray-100 px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{log.reason}</p>
                  <p className="text-xs text-gray-500">关联单：{log.order}</p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${log.amount.startsWith("+") ? "text-emerald-600" : "text-rose-500"}`}>{log.amount}</p>
                  <p className="text-xs text-gray-500">{log.time}</p>
                </div>
              </div>
            ))}
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
                {activeOrder ? `${activeOrder.orderNo} · ${activeOrder.time}` : ""}
              </DialogDescription>
              {activeOrder ? (
                <Badge variant="outline" className="text-teal-700 border-teal-200 bg-teal-50">
                  {activeOrder.status}
                </Badge>
              ) : null}
            </div>
          </DialogHeader>

          {activeOrder && (
            <div className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <Card className="border border-gray-100">
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">订单金额</span>
                      <span className="text-xl font-bold text-gray-900">{activeOrder.amount}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">支付渠道</span>
                      <span className="text-sm text-gray-700">{activeOrder.payChannel}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">配送状态</span>
                      <span className="text-sm text-gray-700">{activeOrder.dispatch}</span>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border border-gray-100">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center gap-3">
                      {activeOrder.driver.avatar ? (
                        <Avatar className="h-12 w-12">
                          <AvatarImage src={activeOrder.driver.avatar} alt={activeOrder.driver.name} />
                          <AvatarFallback>DR</AvatarFallback>
                        </Avatar>
                      ) : (
                        <Avatar className="h-12 w-12">
                          <AvatarFallback>DR</AvatarFallback>
                        </Avatar>
                      )}
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">接单司机</p>
                        <p className="text-sm text-gray-700">{activeOrder.driver.name}</p>
                        <p className="text-xs text-gray-500">{activeOrder.driver.phone}</p>
                      </div>
                      <Badge variant="outline" className="bg-emerald-50 border-emerald-200 text-emerald-700">
                        {activeOrder.driver.status}
                      </Badge>
                    </div>
                    <div className="flex items-start gap-2 text-sm text-gray-700">
                      <MapPin className="h-4 w-4 text-rose-500 mt-0.5" />
                      <span>{activeOrder.address}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Truck className="h-4 w-4 text-indigo-500" />
                  订单状态（参考 SQL：0待支付 1待发货 2待收货 3已完成 4已取消 5已关闭）
                </h4>
                <div className="space-y-2">
                  {activeOrder.steps.map((step, idx) => {
                    const isDone = step.state === "done";
                    const isCurrent = step.state === "current";
                    return (
                      <div key={step.title} className="flex items-start gap-3 rounded-xl px-2 py-1">
                        <div className="mt-0.5 shrink-0">
                          {isDone ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                          ) : isCurrent ? (
                            <Clock className="h-4 w-4 text-amber-500" />
                          ) : (
                            <Circle className="h-4 w-4 text-gray-300" />
                          )}
                        </div>
                        <div className="flex-1 flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">{step.title}</p>
                          <p className="text-xs text-gray-500">{step.time}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3">商品明细</h4>
                <div className="space-y-2">
                  {activeOrder.items.map((item) => (
                    <div
                      key={item.name}
                      className="flex items-center justify-between rounded-xl border border-gray-100 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-900">{item.name}</p>
                        <p className="text-xs text-gray-500">{item.qty}</p>
                      </div>
                      <span className="text-sm font-semibold text-gray-900">{item.price}</span>
                    </div>
                  ))}
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
    </section>
  );
};

export default UserDashboard;
