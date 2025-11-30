import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { mallApi, Product, surfaceMap, categoryMap } from "@/lib/api";

interface PurchaseDialogProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}

export function PurchaseDialog({ isOpen, onClose, product }: PurchaseDialogProps) {
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    address: "",
    quantity: 1,
    notes: ""
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.phone || !formData.address || !product) {
      toast({
        title: "信息不完整",
        description: "请填写完整的联系信息",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      
      // 计算总价
      const totalPrice = product.selling_price * formData.quantity;
      
      // 创建订单
      await mallApi.createOrder({
        customer_phone: formData.phone,
        total_price: totalPrice,
        items: [{
          model: product.model,
          amount: formData.quantity
        }],
        remark: formData.notes || undefined,
        delivery_address: formData.address
      });

      toast({
        title: "订单提交成功！",
        description: "我们会尽快联系您确认订单详情",
      });

      // 重置表单并关闭对话框
      setFormData({
        name: "",
        phone: "",
        address: "",
        quantity: 1,
        notes: ""
      });
      onClose();
      
      // 延迟刷新页面，让用户看到成功提示
      setTimeout(() => {
        window.location.reload();
      }, 1500);
      
    } catch (error) {
      console.error('订单提交失败:', error);
      toast({
        title: "订单提交失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!product) return;
    
    try {
      setLoading(true);
      await mallApi.changeCart({
        model: product.model,
        amount: formData.quantity
      });
      
      toast({
        title: "已添加到购物车",
        description: `${product.model} × ${formData.quantity}`,
      });
      
    } catch (error) {
      console.error('添加购物车失败:', error);
      toast({
        title: "添加购物车失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!product) return null;

  const totalPrice = product.selling_price * formData.quantity;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-gray-800">
            购买 {product.model}
          </DialogTitle>
        </DialogHeader>
        
        {/* 产品信息 */}
        <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
          <img 
            src={product.picture || "https://images.unsplash.com/photo-1615971677499-5467cbab01c2?w=400&h=400&fit=crop"} 
            alt={product.model}
            className="w-20 h-20 object-cover rounded"
          />
          <div className="flex-1">
            <h4 className="font-medium text-gray-800 mb-1">{product.model}</h4>
            <p className="text-sm text-gray-600 mb-1">
              {product.manufacturer} | {product.specification}
            </p>
            <p className="text-sm text-gray-600 mb-1">
              {categoryMap[product.category]} 
              {product.surface ? ` | ${surfaceMap[product.surface]}` : ''}
            </p>
            <p className="text-lg font-bold text-blue-600">¥{product.selling_price}/片</p>
            <p className="text-xs text-gray-500">库存: {product.total_amount}片</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">姓名 *</Label>
              <Input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="请输入您的姓名"
                required
              />
            </div>
            <div>
              <Label htmlFor="phone">电话 *</Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                placeholder="请输入联系电话"
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor="address">收货地址 *</Label>
            <Textarea
              id="address"
              value={formData.address}
              onChange={(e) => handleInputChange('address', e.target.value)}
              placeholder="请输入详细的收货地址"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="quantity">数量（片）</Label>
              <Input
                id="quantity"
                type="number"
                min="1"
                max={product.total_amount}
                value={formData.quantity}
                onChange={(e) => handleInputChange('quantity', parseInt(e.target.value) || 1)}
              />
            </div>
            <div className="flex items-end">
              <div className="text-right">
                <p className="text-sm text-gray-600">总价</p>
                <p className="text-xl font-bold text-blue-600">¥{totalPrice.toFixed(2)}</p>
              </div>
            </div>
          </div>

          <div>
            <Label htmlFor="notes">备注</Label>
            <Textarea
              id="notes"
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              placeholder="其他要求或备注信息（选填）"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex-1"
              disabled={loading}
            >
              取消
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleAddToCart}
              className="flex-1"
              disabled={loading}
            >
              {loading ? "添加中..." : "加入购物车"}
            </Button>
            <Button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? "提交中..." : "立即下单"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
