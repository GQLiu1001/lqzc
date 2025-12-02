import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Ticket, Gift, Clock, Check, Loader2 } from "lucide-react";
import { couponApi, CouponMarket, isLoggedIn } from "@/lib/api";

interface CouponCenterProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginRequired?: () => void;
}

export function CouponCenter({ isOpen, onClose, onLoginRequired }: CouponCenterProps) {
  const [coupons, setCoupons] = useState<CouponMarket[]>([]);
  const [loading, setLoading] = useState(false);
  const [receiving, setReceiving] = useState<number | null>(null);
  const { toast } = useToast();

  // 获取领券中心列表
  const fetchCoupons = async () => {
    try {
      setLoading(true);
      const data = await couponApi.getMarket();
      setCoupons(data);
    } catch (error) {
      console.error("获取优惠券列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 领取优惠券
  const receiveCoupon = async (coupon: CouponMarket) => {
    if (!isLoggedIn()) {
      toast({
        title: "请先登录",
        description: "登录后即可领取优惠券",
        variant: "destructive",
      });
      onClose();
      onLoginRequired?.();
      return;
    }

    if (coupon.is_received) {
      toast({
        title: "已领取",
        description: "您已经领取过该优惠券",
      });
      return;
    }

    try {
      setReceiving(coupon.id);
      await couponApi.receive(coupon.id);
      toast({
        title: "领取成功！",
        description: `${coupon.title} 已放入您的优惠券包`,
      });
      // 更新本地状态
      setCoupons(prev => prev.map(c => 
        c.id === coupon.id ? { ...c, is_received: true } : c
      ));
    } catch (error) {
      toast({
        title: "领取失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setReceiving(null);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchCoupons();
    }
  }, [isOpen]);

  // 获取优惠券类型文字
  const getCouponTypeText = (type: number) => {
    switch (type) {
      case 1: return "满减券";
      case 2: return "折扣券";
      case 3: return "现金券";
      default: return "优惠券";
    }
  };

  // 获取优惠内容描述
  const getCouponDesc = (coupon: CouponMarket) => {
    if (coupon.type === 1 && coupon.threshold_amount && coupon.discount_amount) {
      return `满${coupon.threshold_amount}元减${coupon.discount_amount}元`;
    }
    if (coupon.type === 2 && coupon.discount_rate) {
      return `${(coupon.discount_rate * 10).toFixed(1)}折优惠`;
    }
    if (coupon.type === 3 && coupon.discount_amount) {
      return `立减${coupon.discount_amount}元`;
    }
    return coupon.title;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose} modal={false}>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] bg-gradient-to-br from-rose-50 via-white to-amber-50 overflow-visible">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Gift className="h-6 w-6 text-rose-500" />
            领券中心
          </DialogTitle>
          <DialogDescription>
            限时优惠，先到先得！
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 max-h-[55vh] overflow-y-auto pr-2">
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-rose-500" />
              <span className="ml-2 text-gray-600">加载中...</span>
            </div>
          ) : coupons.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Ticket className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>暂无可领取的优惠券</p>
            </div>
          ) : (
            coupons.map((coupon) => (
              <div
                key={coupon.id}
                className={`relative rounded-xl border-2 overflow-hidden transition-all ${
                  coupon.is_received
                    ? "border-gray-200 bg-gray-50"
                    : "border-rose-200 bg-white hover:shadow-lg hover:border-rose-300"
                }`}
              >
                <div className="flex">
                  {/* 左侧优惠金额 */}
                  <div className={`w-28 flex flex-col items-center justify-center p-4 ${
                    coupon.is_received ? "bg-gray-100" : "bg-gradient-to-br from-rose-500 to-orange-400"
                  }`}>
                    {coupon.type === 2 ? (
                      <>
                        <span className={`text-3xl font-bold ${coupon.is_received ? "text-gray-400" : "text-white"}`}>
                          {((coupon.discount_rate || 0) * 10).toFixed(0)}
                        </span>
                        <span className={`text-sm ${coupon.is_received ? "text-gray-400" : "text-white/90"}`}>折</span>
                      </>
                    ) : (
                      <>
                        <span className={`text-sm ${coupon.is_received ? "text-gray-400" : "text-white/90"}`}>¥</span>
                        <span className={`text-3xl font-bold ${coupon.is_received ? "text-gray-400" : "text-white"}`}>
                          {coupon.discount_amount || 0}
                        </span>
                      </>
                    )}
                    <Badge variant="secondary" className={`mt-1 text-xs ${
                      coupon.is_received ? "bg-gray-200 text-gray-500" : "bg-white/20 text-white"
                    }`}>
                      {getCouponTypeText(coupon.type)}
                    </Badge>
                  </div>
                  
                  {/* 右侧信息 */}
                  <div className="flex-1 p-4">
                    <h4 className={`font-semibold text-lg ${coupon.is_received ? "text-gray-400" : "text-gray-800"}`}>
                      {coupon.title}
                    </h4>
                    <p className={`text-sm mt-1 ${coupon.is_received ? "text-gray-400" : "text-gray-600"}`}>
                      {getCouponDesc(coupon)}
                    </p>
                    <div className={`flex items-center gap-1 mt-2 text-xs ${coupon.is_received ? "text-gray-400" : "text-gray-500"}`}>
                      <Clock className="h-3 w-3" />
                      <span>有效期：{coupon.valid_from} 至 {coupon.valid_to}</span>
                    </div>
                  </div>
                  
                  {/* 领取按钮 */}
                  <div className="flex items-center pr-4">
                    <Button
                      size="sm"
                      disabled={coupon.is_received || receiving === coupon.id}
                      onClick={() => receiveCoupon(coupon)}
                      className={coupon.is_received 
                        ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                        : "bg-rose-500 hover:bg-rose-600 text-white"
                      }
                    >
                      {receiving === coupon.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : coupon.is_received ? (
                        <>
                          <Check className="h-4 w-4 mr-1" />
                          已领取
                        </>
                      ) : (
                        "立即领取"
                      )}
                    </Button>
                  </div>
                </div>
                
                {/* 装饰性锯齿边 */}
                <div className="absolute left-28 top-0 bottom-0 w-2">
                  <div className="h-full flex flex-col justify-around">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className={`w-2 h-2 rounded-full ${coupon.is_received ? "bg-gray-50" : "bg-rose-50"}`} />
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

