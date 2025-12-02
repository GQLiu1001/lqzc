import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { ShoppingCart, Trash2, Minus, Plus, Loader2 } from "lucide-react";
import { mallApi, cartApi, CartItem, Product, isLoggedIn } from "@/lib/api";

// 增强的购物车项，包含完整商品信息和前端计算的价格
interface EnhancedCartItem extends CartItem {
  manufacturer?: string;
  specification?: string;
  category?: number;
  picture?: string;
  calculated_subtotal: number; // 前端计算的小计
}

interface CartDropdownProps {
  onOrderClick?: () => void;
  cartItems: { [key: string]: number }; // 从外部传入的购物车数据
  onCartChange?: () => void; // 购物车变化时的回调函数
}

export function CartDropdown({ onOrderClick, cartItems: externalCartItems, onCartChange }: CartDropdownProps) {
  const [cartItems, setCartItems] = useState<EnhancedCartItem[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]); // 存储所有商品信息用于价格计算
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [buttonRef, setButtonRef] = useState<HTMLButtonElement | null>(null);
  const cartRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // 计算外部购物车的总数量（用于徽章显示）
  const externalTotalItems = Object.values(externalCartItems).reduce((sum, amount) => sum + amount, 0);

  // 获取所有商品信息用于价格计算
  const fetchAllProducts = async () => {
    try {
      const response = await mallApi.getProductList({ size: 1000 }); // 获取所有商品
      setAllProducts(response.records);
    } catch (error) {
      console.error('获取商品信息失败:', error);
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
      const enhancedItems: EnhancedCartItem[] = backendCartItems
        .filter(cartItem => cartItem && cartItem.model) // 过滤无效项
        .map(cartItem => {
          const product = products.find(p => p.model === cartItem.model);
          const sellingPrice = product?.selling_price || 0;
          
          return {
            ...cartItem,
            selling_price: sellingPrice, // 使用商品展示接口的价格
            manufacturer: product?.manufacturer,
            specification: product?.specification,
            category: product?.category,
            picture: product?.picture,
            calculated_subtotal: sellingPrice * (cartItem.amount || 0) // 前端计算小计
          };
        });
      
      setCartItems(enhancedItems);
    } catch (error) {
      console.error('获取购物车失败:', error);
      // 设置空购物车，不显示错误提示
      setCartItems([]);
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
      onCartChange?.(); // 通知主页面购物车已变化
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
      onCartChange?.(); // 通知主页面购物车已变化
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

  // 监听下拉菜单打开状态
  useEffect(() => {
    if (isOpen) {
      fetchCart();
    }
  }, [isOpen]);

  // 点击外部关闭购物车
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && 
          cartRef.current && 
          !cartRef.current.contains(event.target as Node) &&
          buttonRef && 
          !buttonRef.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, buttonRef]);

  // 计算购物车菜单位置
  const getMenuPosition = () => {
    if (!buttonRef) return { top: '5rem', right: '1rem' };
    
    const rect = buttonRef.getBoundingClientRect();
    const menuWidth = 400;
    const viewportWidth = window.innerWidth;
    
    // 确保菜单不会超出屏幕右边界
    const rightSpace = viewportWidth - rect.right;
    const leftPosition = rightSpace < menuWidth ? rect.left - menuWidth + rect.width : rect.right - menuWidth;
    
    return {
      top: `${rect.bottom + 8}px`, // 按钮下方8px
      left: `${Math.max(16, leftPosition)}px`, // 确保不会超出左边界
    };
  };

  const totalPrice = cartItems.reduce((sum, item) => sum + (item.calculated_subtotal || 0), 0);
  const totalItems = cartItems.reduce((sum, item) => sum + (item.amount || 0), 0);

  const menuPosition = getMenuPosition();

  return (
    <>
      {/* 购物车按钮 */}
      <Button 
        variant="ghost" 
        size="lg"
        className="text-gray-700 hover:bg-gray-100/50 backdrop-blur-sm relative h-12 w-12"
        onClick={() => setIsOpen(!isOpen)}
        ref={setButtonRef}
      >
        <ShoppingCart className="h-7 w-7" />
        <span 
          className={`absolute -top-1 -right-1 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center transition-all duration-200 ${
            externalTotalItems > 0 
              ? 'bg-red-500 opacity-100 scale-100' 
              : 'bg-red-500 opacity-0 scale-75'
          }`}
        >
          {externalTotalItems > 99 ? '99+' : externalTotalItems || '0'}
        </span>
      </Button>

      {/* 浮动购物车下拉菜单 */}
      {isOpen && (
        <div 
          ref={cartRef}
          className="fixed z-50 w-[400px] max-h-[500px] bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden"
          style={{
            top: menuPosition.top,
            left: menuPosition.left,
            opacity: 1,
          }}
        >
          <div className="p-4 border-b bg-gray-50">
            <h3 className="font-semibold text-gray-800">
              购物车 ({cartItems.length}件商品)
            </h3>
            {totalPrice > 0 && (
              <p className="text-sm text-gray-600">
                合计: <span className="font-bold text-blue-600">¥{(totalPrice || 0).toFixed(2)}</span>
              </p>
            )}
          </div>

          {loading && (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-600">加载中...</span>
            </div>
          )}

          {!loading && cartItems.length === 0 && (
            <div className="text-center py-8">
              <ShoppingCart className="h-12 w-12 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-600">购物车为空</p>
              <p className="text-sm text-gray-500 mt-1">快去选购喜欢的商品吧！</p>
            </div>
          )}

          {!loading && cartItems.length > 0 && (
            <>
              {/* 购物车商品列表 */}
              <div className="max-h-[300px] overflow-y-auto">
                {cartItems.map((item) => (
                  <div key={item.model} className="flex items-center gap-3 p-4 border-b bg-gray-50 hover:bg-gray-100">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-800 truncate">{item.model}</h4>
                      <p className="text-sm text-gray-600">¥{item.selling_price || 0} × {item.amount || 0}</p>
                      <p className="text-sm font-bold text-blue-600">¥{(item.calculated_subtotal || 0).toFixed(2)}</p>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => updateCartItem(item.model, item.amount - 1)}
                        disabled={updating === item.model}
                        className="h-6 w-6"
                      >
                        <Minus className="h-3 w-3" />
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
                        className="w-12 text-center text-sm font-medium border rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => updateCartItem(item.model, item.amount + 1)}
                        disabled={updating === item.model}
                        className="h-6 w-6"
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeCartItem(item.model)}
                        disabled={updating === item.model}
                        className="h-6 w-6 text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        {updating === item.model ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <Trash2 className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* 底部操作按钮 */}
              <div className="p-4 bg-gray-50">
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setIsOpen(false)}
                  >
                    继续购物
                  </Button>
                  <Button
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                    onClick={() => {
                      setIsOpen(false);
                      onOrderClick?.();
                    }}
                  >
                    去结算
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
} 