import { useState, useEffect } from "react";
import { X, Volume2, Gift } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Announcement {
  id: number;
  text: string;
  type: "coupon" | "promotion" | "notice";
  link?: string;
}

interface AnnouncementBannerProps {
  onCouponClick?: () => void;
}

export function AnnouncementBanner({ onCouponClick }: AnnouncementBannerProps) {
  const [visible, setVisible] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // 公告列表 - 后续可从后端API获取
  const announcements: Announcement[] = [
    { id: 1, text: "🎉 新用户专享：注册即送满299减30优惠券！", type: "coupon" },
    { id: 2, text: "🔥 限时抢券：全场通用券限量发放中，先到先得！", type: "coupon" },
    { id: 3, text: "📢 双十二大促：全场瓷砖低至8折，活动截止12月12日", type: "promotion" },
  ];

  // 自动轮播
  useEffect(() => {
    if (announcements.length <= 1) return;
    
    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % announcements.length);
    }, 4000);
    
    return () => clearInterval(interval);
  }, [announcements.length]);

  if (!visible || announcements.length === 0) return null;

  const currentAnnouncement = announcements[currentIndex];

  return (
    <div className="fixed top-[73px] left-0 right-0 z-40 bg-gradient-to-r from-rose-500 via-orange-500 to-amber-500 text-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2 flex-1 overflow-hidden">
            <Volume2 className="h-4 w-4 shrink-0 animate-pulse" />
            <div 
              className="flex-1 overflow-hidden cursor-pointer"
              onClick={() => {
                if (currentAnnouncement.type === "coupon") {
                  onCouponClick?.();
                }
              }}
            >
              <div 
                className="whitespace-nowrap animate-marquee hover:pause-animation"
                style={{ 
                  animation: "marquee 15s linear infinite",
                }}
              >
                <span className="font-medium">{currentAnnouncement.text}</span>
                {currentAnnouncement.type === "coupon" && (
                  <span className="ml-2 text-white/90 underline">点击领取 →</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2 shrink-0 ml-4">
            {currentAnnouncement.type === "coupon" && (
              <Button
                size="sm"
                variant="secondary"
                className="bg-white/20 hover:bg-white/30 text-white border-white/30 h-7 text-xs"
                onClick={onCouponClick}
              >
                <Gift className="h-3 w-3 mr-1" />
                领券中心
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-white/80 hover:text-white hover:bg-white/20"
              onClick={() => setVisible(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
      
      {/* 进度指示器 */}
      {announcements.length > 1 && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/20">
          <div 
            className="h-full bg-white/50 transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / announcements.length) * 100}%` }}
          />
        </div>
      )}
      
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .pause-animation:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}

