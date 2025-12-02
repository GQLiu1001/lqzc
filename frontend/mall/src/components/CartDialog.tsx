import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Trash2, Minus, Plus, Loader2, MapPin } from "lucide-react";
import { mallApi, cartApi, authApi, addressApi, CartItem, Product, Address, isLoggedIn } from "@/lib/api";

// 增强的购物车项，包含完整商品信息和前端计算的价格
interface EnhancedCartItem extends CartItem {
  manufacturer?: string;
  specification?: string;
  category?: number;
  picture?: string;
  calculated_subtotal: number; // 前端计算的小计
}

interface CartDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CartDialog({ isOpen, onClose }: CartDialogProps) {
  const [cartItems, setCartItems] = useState<EnhancedCartItem[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]); // 存储所有商品信息用于价格计算
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);
  const [orderForm, setOrderForm] = useState({
    name: "",
    phone: "",
    address: "",
    addressId: "",
    notes: ""
  });
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [addressLoading, setAddressLoading] = useState(false);
  const { toast } = useToast();

  // 获取用户信息和地址列表
  const fetchUserAndAddresses = async () => {
    if (!isLoggedIn()) return;
    
    try {
      setAddressLoading(true);
      
      // 并行获取用户信息和地址列表
      const [profile, addressList] = await Promise.all([
        authApi.getProfile(),
        addressApi.getAddressList()
      ]);
      
      setAddresses(addressList);
      
      // 找到默认地址
      const defaultAddress = addressList.find(addr => addr.is_default === 1);
      
      // 自动填充表单
      setOrderForm(prev => ({
        ...prev,
        name: defaultAddress?.receiver_name || profile.nickname || "",
        phone: defaultAddress?.receiver_phone || profile.phone || "",
        address: defaultAddress 
          ? `${defaultAddress.province}${defaultAddress.city}${defaultAddress.district}${defaultAddress.detail}`
          : "",
        addressId: defaultAddress?.id?.toString() || ""
      }));
    } catch (error) {
      console.error("获取用户信息失败:", error);
    } finally {
      setAddressLoading(false);
    }
  };

  // 选择地址时更新表单
  const handleAddressSelect = (addressId: string) => {
    const selectedAddress = addresses.find(addr => addr.id?.toString() === addressId);
    if (selectedAddress) {
      setOrderForm(prev => ({
        ...prev,
        name: selectedAddress.receiver_name,
        phone: selectedAddress.receiver_phone,
        address: `${selectedAddress.province}${selectedAddress.city}${selectedAddress.district}${selectedAddress.detail}`,
        addressId: addressId
      }));
    }
  };

  // 获取购物车数据并计算价格（需要登录）
  const fetchCart = async () => {
    // 未登录时不获取购物车
    if (!isLoggedIn()) {
      setCartItems([]);
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      
      // 获取后端购物车数据
      const backendCartItems = await cartApi.getCart();
      
      // 安全处理空购物车
      if (!backendCartItems || !Array.isArray(backendCartItems) || backendCartItems.length === 0) {
        setCartItems([]);
        return;
      }
      
      // 如果还没有商品信息，先获取
      let products = allProducts;
      if (products.length === 0) {
        const response = await mallApi.getProductList({ size: 1000 });
        products = response.records;
        setAllProducts(products);
      }
      
      // 增强购物车数据，添加商品信息和计算价格
      const enhancedItems: EnhancedCartItem[] = backendCartItems.map(cartItem => {
        const product = products.find(p => p.model === cartItem.model);
        const sellingPrice = product?.selling_price || 0;
        
        return {
          ...cartItem,
          selling_price: sellingPrice, // 使用商品展示接口的价格
          manufacturer: product?.manufacturer,
          specification: product?.specification,
          category: product?.category,
          picture: product?.picture,
          calculated_subtotal: sellingPrice * cartItem.amount // 前端计算小计
        };
      });
      
      setCartItems(enhancedItems);
    } catch (error) {
      console.error('获取购物车失败:', error);
      toast({
        title: "获取购物车失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // 更新购物车商品数量
  const updateCartItem = async (model: string, newAmount: number) => {
    if (newAmount <= 0) {
      await removeCartItem(model);
      return;
    }

    try {
      setUpdating(model);
      await cartApi.changeCart({ model, amount: newAmount });
      await fetchCart(); // 重新获取购物车数据
    } catch (error) {
      console.error('更新购物车失败:', error);
      toast({
        title: "更新失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setUpdating(null);
    }
  };

  // 删除购物车商品
  const removeCartItem = async (model: string) => {
    try {
      setUpdating(model);
      await cartApi.deleteCartItem({ model });
      await fetchCart(); // 重新获取购物车数据
      toast({
        title: "已移除商品",
        description: `${model} 已从购物车移除`,
      });
    } catch (error) {
      console.error('删除购物车商品失败:', error);
      toast({
        title: "删除失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setUpdating(null);
    }
  };

  // 提交订单
  const submitOrder = async () => {
    if (!orderForm.name || !orderForm.phone || !orderForm.address) {
      toast({
        title: "信息不完整",
        description: "请填写完整的联系信息",
        variant: "destructive"
      });
      return;
    }

    if (cartItems.length === 0) {
      toast({
        title: "购物车为空",
        description: "请先添加商品到购物车",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      
      const totalPrice = cartItems.reduce((sum, item) => sum + (item.calculated_subtotal || 0), 0);
      
      await cartApi.createOrder({
        customer_phone: orderForm.phone,
        total_price: totalPrice,
        items: cartItems.map(item => ({
          model: item.model,
          amount: item.amount
        })),
        remark: orderForm.notes || undefined,
        delivery_address: orderForm.address
      });

      toast({
        title: "订单提交成功！",
        description: "我们会尽快联系您确认订单详情",
      });

      // 重置表单并关闭对话框
      setOrderForm({
        name: "",
        phone: "",
        address: "",
        addressId: "",
        notes: ""
      });
      setShowOrderForm(false);
      onClose();
      
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

  // 监听对话框打开状态
  useEffect(() => {
    if (isOpen) {
      fetchCart();
    }
  }, [isOpen]);

  // 进入订单表单时获取用户信息和地址
  useEffect(() => {
    if (showOrderForm) {
      fetchUserAndAddresses();
    }
  }, [showOrderForm]);

  const totalPrice = cartItems.reduce((sum, item) => sum + (item.calculated_subtotal || 0), 0);

  return (
    <Dialog open={isOpen} onOpenChange={onClose} modal={false}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] bg-white/95 backdrop-blur overflow-visible">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-gray-800">
            购物车 ({cartItems.length}件商品)
          </DialogTitle>
        </DialogHeader>

        {loading && !showOrderForm && (
          <div className="flex justify-center items-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">加载中...</span>
          </div>
        )}

        {!loading && !showOrderForm && (
          <>
            {cartItems.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600">购物车为空</p>
                <p className="text-sm text-gray-500 mt-2">快去选购喜欢的商品吧！</p>
              </div>
            ) : (
              <>
                {/* 购物车商品列表 */}
                <div className="space-y-4 max-h-[400px] overflow-y-auto">
                  {cartItems.map((item) => (
                    <div key={item.model} className="flex items-center gap-4 p-4 border rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-800">{item.model}</h4>
                        <p className="text-sm text-gray-600">单价: ¥{item.selling_price || 0}</p>
                        <p className="text-lg font-bold text-blue-600">小计: ¥{(item.calculated_subtotal || 0).toFixed(2)}</p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => updateCartItem(item.model, item.amount - 1)}
                          disabled={updating === item.model}
                          className="h-8 w-8"
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        
                        <input
                          type="number"
                          min="1"
                          max="9999"
                          value={item.amount || 0}
                          onChange={(e) => {
                            const newAmount = parseInt(e.target.value) || 0;
                            if (newAmount > 0) {
                              updateCartItem(item.model, newAmount);
                            }
                          }}
                          disabled={updating === item.model}
                          className="w-16 text-center font-medium border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                        
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => updateCartItem(item.model, item.amount + 1)}
                          disabled={updating === item.model}
                          className="h-8 w-8"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => removeCartItem(item.model)}
                          disabled={updating === item.model}
                          className="h-8 w-8 text-red-600 hover:text-red-700"
                        >
                          {updating === item.model ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* 总价和操作按钮 */}
                <div className="border-t pt-4">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-lg font-medium">总计:</span>
                    <span className="text-2xl font-bold text-blue-600">¥{(totalPrice || 0).toFixed(2)}</span>
                  </div>
                  
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      onClick={onClose}
                      className="flex-1"
                    >
                      继续购物
                    </Button>
                    <Button
                      onClick={() => setShowOrderForm(true)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                    >
                      结算订单
                    </Button>
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* 订单表单 */}
        {showOrderForm && (
          <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
            <div className="border-b pb-4">
              <h3 className="font-medium text-gray-800 mb-2">订单信息</h3>
              <p className="text-sm text-gray-600">
                共 {cartItems.length} 件商品，总计 ¥{(totalPrice || 0).toFixed(2)}
              </p>
            </div>

            {/* 地址选择 */}
            {addresses.length > 0 && (
              <div>
                <Label className="flex items-center gap-1 mb-2">
                  <MapPin className="h-4 w-4 text-rose-500" />
                  选择收货地址
                </Label>
                <Select value={orderForm.addressId} onValueChange={handleAddressSelect}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={addressLoading ? "加载中..." : "选择已保存的地址"} />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={4} className="z-[9999]">
                    {addresses.map((addr) => (
                      <SelectItem key={addr.id} value={addr.id?.toString() || ""}>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{addr.receiver_name}</span>
                          <span className="text-gray-500">{addr.receiver_phone}</span>
                          {addr.is_default === 1 && (
                            <span className="text-xs bg-blue-100 text-blue-600 px-1 rounded">默认</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 truncate max-w-[300px]">
                          {addr.province}{addr.city}{addr.district}{addr.detail}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="order-name">姓名 *</Label>
                <Input
                  id="order-name"
                  type="text"
                  value={orderForm.name}
                  onChange={(e) => setOrderForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="请输入您的姓名"
                  required
                />
              </div>
              <div>
                <Label htmlFor="order-phone">电话 *</Label>
                <Input
                  id="order-phone"
                  type="tel"
                  value={orderForm.phone}
                  onChange={(e) => setOrderForm(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="请输入联系电话"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="order-address">收货地址 *</Label>
              <Textarea
                id="order-address"
                value={orderForm.address}
                onChange={(e) => setOrderForm(prev => ({ ...prev, address: e.target.value, addressId: "" }))}
                placeholder="请输入详细的收货地址"
                required
              />
            </div>

            <div>
              <Label htmlFor="order-notes">备注</Label>
              <Textarea
                id="order-notes"
                value={orderForm.notes}
                onChange={(e) => setOrderForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="其他要求或备注信息（选填）"
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowOrderForm(false)}
                className="flex-1"
                disabled={loading}
              >
                返回购物车
              </Button>
              <Button
                onClick={submitOrder}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? "提交中..." : "确认下单"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
} 