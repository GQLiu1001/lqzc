import { useState, useEffect } from "react";
import { Search, Filter, ShoppingCart, Phone, MapPin, Loader2, Plus, Minus, Settings, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PurchaseDialog } from "@/components/PurchaseDialog";
import { CartDialog } from "@/components/CartDialog";
import { CartDropdown } from "@/components/CartDropdown";
import { Toaster } from "@/components/ui/toaster";
import AIAssistant from "@/components/AIAssistant";
import { useToast } from "@/hooks/use-toast";
import { mallApi, Product, surfaceMap, categoryMap } from "@/lib/api";
import UserDashboard from "@/components/UserDashboard";

const Index = () => {
  const [selectedCategory, setSelectedCategory] = useState("全部");
  const [selectedSurface, setSelectedSurface] = useState("全部");
  const [searchTerm, setSearchTerm] = useState("");
  const [purchaseDialogOpen, setPurchaseDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [cartDialogOpen, setCartDialogOpen] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [productQuantities, setProductQuantities] = useState<{ [key: string]: number }>({}); // 每个商品的数量
  const [addingToCart, setAddingToCart] = useState<string | null>(null); // 正在添加到购物车的商品
  const [cartItems, setCartItems] = useState<{ [key: string]: number }>({}); // 购物车中的商品数量
  const [currentBgImage, setCurrentBgImage] = useState(0); // 当前背景图片索引
  const [isSearchExpanded, setIsSearchExpanded] = useState(false); // 搜索区域是否展开
  const [activeSection, setActiveSection] = useState<"mall" | "user">("mall");
  const pageSize = 12;
  
  const { toast } = useToast();

  // 背景图片URL数组
  const backgroundImages = [
    'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed3.png',
    'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed2.png',
    'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed1.png',
    'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed4.png',
    'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed5.png',
    'https://pub-061d1fd03ea74e68849f186c401fde40.r2.dev/unnamed6.png'
  ];

  const categories = [
    "全部", "墙砖", "地砖", "胶", "洁具"
  ];

  const surfaceTypes = [
    "全部", "抛光", "哑光", "釉面", "通体大理石", "微晶石", "岩板"
  ];

  // 获取购物车数据
  const fetchCartItems = async () => {
    try {
      const cartData = await mallApi.getCart();
      const cartMap: { [key: string]: number } = {};
      
      // 安全处理购物车数据，防止null或undefined
      if (cartData && Array.isArray(cartData)) {
        cartData.forEach(item => {
          if (item && item.model && typeof item.amount === 'number') {
            cartMap[item.model] = item.amount;
          }
        });
      }
      
      setCartItems(cartMap);
    } catch (error) {
      console.error('获取购物车失败:', error);
      // 静默失败，不显示错误提示，设置空购物车
      setCartItems({});
    }
  };

  // 获取商品列表
  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await mallApi.getProductList({
        current: currentPage,
        size: pageSize,
        category: selectedCategory,
        surface: selectedSurface
      });
      
      if (currentPage === 1) {
        // 第一页，直接设置
        setProducts(response.records);
      } else {
        // 加载更多，去重后追加
        setProducts(prev => {
          const existingModels = new Set(prev.map(p => p.model));
          const newProducts = response.records.filter(p => !existingModels.has(p.model));
          return [...prev, ...newProducts];
        });
      }
      
      setTotal(response.total);
      
      // 同时获取购物车数据
      await fetchCartItems();
    } catch (error) {
      console.error('获取商品列表失败:', error);
      toast({
        title: "获取商品列表失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // 监听筛选条件变化
  useEffect(() => {
    setCurrentPage(1); // 重置页码
    fetchProducts();
  }, [selectedCategory, selectedSurface]);

  // 监听页码变化
  useEffect(() => {
    if (currentPage !== 1) {
      fetchProducts();
    }
  }, [currentPage]);

  // 初始加载
  useEffect(() => {
    fetchProducts();
  }, []);

  // 背景图片自动轮播
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentBgImage(prev => (prev + 1) % backgroundImages.length);
    }, 3000); // 每3秒切换一次

    return () => clearInterval(interval);
  }, [backgroundImages.length]);

  // 本地搜索过滤（在API结果基础上进行文本搜索）
  const filteredProducts = products.filter(product => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    const model = product.model || '';
    const manufacturer = product.manufacturer || '';
    const specification = product.specification || '';
    
    return model.toLowerCase().includes(searchLower) ||
           manufacturer.toLowerCase().includes(searchLower) ||
           specification.toLowerCase().includes(searchLower);
  });

  const handlePurchase = (product: Product) => {
    setSelectedProduct(product);
    setPurchaseDialogOpen(true);
  };

  // 获取表面处理显示文本
  const getSurfaceDisplay = (surface: number) => {
    return surfaceMap[surface] || '未知';
  };

  // 获取分类显示文本
  const getCategoryDisplay = (category: number) => {
    return categoryMap[category] || '未知';
  };

  // 获取商品单位
  const getProductUnit = (category: number) => {
    switch (category) {
      case 1: // 墙砖
      case 2: // 地砖
        return '每片';
      case 3: // 胶
        return '每桶';
      case 4: // 洁具
        return '每个';
      default:
        return '每片';
    }
  };

  // 获取规格显示（胶类商品显示"-"）
  const getSpecificationDisplay = (category: number, specification: string) => {
    return category === 3 ? '-' : specification;
  };

  // 获取表面处理显示（胶和洁具显示"-"）
  const getSurfaceDisplayForProduct = (category: number, surface: number) => {
    if (category === 3 || category === 4) {
      return '-';
    }
    return surface ? getSurfaceDisplay(surface) : '-';
  };

  const switchToMall = () => {
    setActiveSection("mall");
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const openUserCenter = () => {
    setActiveSection("user");
    setIsSearchExpanded(false);
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // 加载更多产品
  const loadMore = () => {
    setCurrentPage(prev => prev + 1);
  };

  // 获取商品数量
  const getProductQuantity = (model: string) => {
    // 如果用户有输入数量，优先显示用户输入的数量
    if (productQuantities[model]) {
      return productQuantities[model];
    }
    // 如果商品在购物车中且用户没有输入，显示购物车中的数量
    if (cartItems[model]) {
      return cartItems[model];
    }
    // 默认为1
    return 1;
  };

  // 检查商品是否在购物车中
  const isInCart = (model: string) => {
    return cartItems[model] > 0;
  };

  // 设置商品数量（只更新本地状态，不直接调用API）
  const setProductQuantity = (model: string, quantity: number) => {
    if (quantity < 1) quantity = 1;
    if (quantity > 9999) quantity = 9999;
    
    // 只更新本地状态，不直接调用API
    setProductQuantities(prev => ({
      ...prev,
      [model]: quantity
    }));
  };

  // 滚动到联系我们部分
  const scrollToContact = () => {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  // 滚动到页面顶部并展开搜索
  const handleSearchClick = () => {
    const willExpand = !isSearchExpanded;
    setActiveSection("mall");
    // 无论展开还是收起，都清空搜索条件
    setSearchTerm('');
    setIsSearchExpanded(willExpand);
    if (willExpand) {
      // 如果是展开搜索，滚动到页面顶部
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  // 添加到购物车或更新数量
  const addToCart = async (product: Product) => {
    const quantity = getProductQuantity(product.model);
    const inCart = isInCart(product.model);
    
    try {
      setAddingToCart(product.model);
      await mallApi.changeCart({
        model: product.model,
        amount: quantity
      });
      
      // 更新本地购物车状态
      setCartItems(prev => ({
        ...prev,
        [product.model]: quantity
      }));
      
      toast({
        title: inCart ? "数量已更新" : "已添加到购物车",
        description: `${product.model} × ${quantity}`,
      });
      
      // 清除用户的本地输入，让界面显示购物车中的实际数量
      setProductQuantities(prev => {
        const newState = { ...prev };
        delete newState[product.model]; // 删除本地输入，让界面显示购物车数量
        return newState;
      });
    } catch (error) {
      console.error(inCart ? '更新购物车失败:' : '添加购物车失败:', error);
      toast({
        title: inCart ? "更新失败" : "添加购物车失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      });
    } finally {
      setAddingToCart(null);
    }
  };

  // 当选择胶或洁具时，重置表面处理为"全部"
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    if (category === '胶' || category === '洁具' || category === '全部') {
      setSelectedSurface('全部');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative w-full">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/30 backdrop-blur-xl border-b border-gray-200/30 shadow-lg w-full">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 cursor-pointer" onClick={switchToMall}>
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg"></div>
              <h1 className="text-2xl font-bold text-gray-800">陶选</h1>
            </div>
            <nav className="hidden md:flex items-center space-x-8 text-gray-700">
              <span className="text-xl font-medium text-gray-800">打造您的理想空间</span>
              {/* 桌面端搜索按钮 */}
              <Button 
                variant="ghost" 
                size="sm"
                className="hidden lg:flex text-gray-700 hover:bg-gray-100/50 backdrop-blur-sm"
                onClick={handleSearchClick}
              >
                <Search className="h-4 w-4 mr-2" />
                搜索
              </Button>
              {/* 中等屏幕搜索按钮 */}
              <Button 
                variant="ghost" 
                size="sm"
                className="lg:hidden text-gray-700 hover:bg-gray-100/50 backdrop-blur-sm"
                onClick={handleSearchClick}
                title="搜索"
              >
                <Search className="h-5 w-5" />
              </Button>
            </nav>
            <div className="flex items-center space-x-3">
              {/* 移动端搜索按钮 */}
              <Button 
                variant="ghost" 
                size="lg"
                className="md:hidden text-gray-700 hover:bg-gray-100/50 backdrop-blur-sm h-12 w-12"
                onClick={handleSearchClick}
                title="搜索"
              >
                <Search className="h-6 w-6" />
              </Button>
              
              {/* 管理后台按钮 */}
              <Button 
                variant="ghost" 
                size="lg"
                className="text-gray-700 hover:bg-gray-100/50 backdrop-blur-sm h-12 w-12"
                onClick={() => window.open('/admin/', '_blank')}
                title="管理后台"
              >
                <Settings className="h-6 w-6" />
              </Button>

              {/* 用户中心入口 */}
              <Button 
                variant="ghost" 
                size="lg"
                className={`h-12 w-12 backdrop-blur-sm border transition-colors ${
                  activeSection === 'user'
                    ? 'bg-blue-50 border-blue-100 text-blue-700 hover:bg-blue-100/70'
                    : 'text-gray-700 hover:bg-gray-100/50 border-transparent'
                }`}
                onClick={openUserCenter}
                title="用户中心"
              >
                <UserRound className="h-6 w-6" />
              </Button>
              
              <Button 
                variant="ghost" 
                size="lg"
                className="text-gray-700 hover:bg-gray-100/50 backdrop-blur-sm h-12 w-12"
                onClick={scrollToContact}
                title="联系我们"
              >
                <Phone className="h-7 w-7" />
              </Button>
              <CartDropdown 
                onOrderClick={() => setCartDialogOpen(true)} 
                cartItems={cartItems}
                onCartChange={fetchCartItems}
              />
            </div>
          </div>
        </div>
      </header>

      {activeSection === 'mall' ? (
        <>
          {/* Hero Section */}
          <section className="hero-section relative mx-auto px-4 py-40 text-center overflow-hidden min-h-[600px]">
            {/* 背景图片层叠 */}
            {backgroundImages.map((image, index) => (
              <div
                key={index}
                className={`absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-1000 ${
                  index === currentBgImage ? 'opacity-100' : 'opacity-0'
                }`}
                style={{
                  backgroundImage: `url(${image})`,
                }}
              />
            ))}
            
            {/* 遮罩层 */}
            <div className="absolute inset-0 bg-white/50" />
            
            {/* 内容层 */}
            <div className="relative z-10 container mx-auto">
              {/* 搜索区域 - 根据状态显示/隐藏 */}
              {isSearchExpanded && (
                <div className="max-w-2xl mx-auto bg-white/30 backdrop-blur-xl rounded-2xl p-8 border border-gray-200/50 shadow-xl transform transition-all duration-300 ease-in-out">
                  <p className="text-xl text-gray-800 mb-6 font-bold drop-shadow-lg text-center">
                    专业瓷砖供应商，为您提供高品质的地板砖、墙面砖等产品
                  </p>
                  
                  {/* Search Bar */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-1 relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                      <Input
                        type="text"
                        placeholder="搜索产品型号、制造商或规格..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 bg-white/60 border-gray-200 text-gray-800 placeholder:text-gray-400 focus:bg-white/80 backdrop-blur-sm"
                      />
                    </div>
                    <Button className="bg-blue-600 text-white hover:bg-blue-700">
                      <Filter className="h-4 w-4 mr-2" />
                      筛选
                    </Button>
                  </div>
                </div>
              )}
            </div>
            
            {/* 轮播指示器 */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2 z-20">
              {backgroundImages.map((_, index) => (
                <button
                  key={index}
                  className={`w-3 h-3 rounded-full transition-all ${
                    index === currentBgImage ? 'bg-blue-600' : 'bg-white/50'
                  }`}
                  onClick={() => setCurrentBgImage(index)}
                />
              ))}
            </div>
          </section>

          {/* Products Section */}
          <section className="container mx-auto px-4 pb-16">
            <div className="bg-white/90 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-gray-200/50">
              {/* Categories and Surface Types - 垂直重叠显示 */}
              <div className="mb-8 space-y-8">
                {/* 产品分类 */}
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-gray-800 mb-6">产品分类</h3>
                  <div className="flex flex-wrap gap-3 justify-center">
                    {categories.map((category) => (
                      <Button
                        key={category}
                        variant={selectedCategory === category ? "default" : "outline"}
                        onClick={() => handleCategoryChange(category)}
                        className={`rounded-full ${
                          selectedCategory === category
                            ? "bg-blue-600 hover:bg-blue-700 text-white"
                            : "text-gray-600 hover:bg-blue-50 border-gray-200"
                        }`}
                      >
                        {category}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* 表面处理 - 只在选择墙砖或地砖时显示 */}
                {(selectedCategory === '墙砖' || selectedCategory === '地砖') && (
                  <div className="text-center">
                    <h3 className="text-2xl font-bold text-gray-800 mb-6">表面处理</h3>
                    <div className="flex flex-wrap gap-3 justify-center">
                      {surfaceTypes.map((surface) => (
                        <Button
                          key={surface}
                          variant={selectedSurface === surface ? "default" : "outline"}
                          onClick={() => setSelectedSurface(surface)}
                          className={`rounded-full ${
                            selectedSurface === surface
                              ? "bg-green-600 hover:bg-green-700 text-white"
                              : "text-gray-600 hover:bg-green-50 border-gray-200"
                          }`}
                        >
                          {surface}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Loading State */}
              {loading && (
                <div className="flex justify-center items-center py-16">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  <span className="ml-2 text-gray-600">加载中...</span>
                </div>
              )}

              {/* Product Grid */}
              {!loading && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredProducts.map((product, index) => (
                      <Card key={`${product.model}-${index}`} className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-0 shadow-lg bg-white/95 backdrop-blur-sm">
                        <CardContent className="p-0">
                          <div className="relative overflow-hidden rounded-t-lg">
                            <img
                              src={product.picture || "https://images.unsplash.com/photo-1615971677499-5467cbab01c2?w=400&h=400&fit=crop"}
                              alt={product.model}
                              className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-300"
                            />
                            <Badge className="absolute top-3 left-3 bg-blue-600 hover:bg-blue-700 text-white">
                              {getCategoryDisplay(product.category)}
                            </Badge>
                            <Badge className="absolute top-3 right-3 bg-green-600 hover:bg-green-700 text-white">
                              库存: {product.total_amount}
                            </Badge>
                          </div>
                          <div className="p-6">
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex-1">
                                <h4 className="font-bold text-gray-800 text-xl mb-1 group-hover:text-blue-600 transition-colors">
                                  {product.model}
                                </h4>
                                <p className="text-sm text-gray-600 mb-2">型号</p>
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-bold text-blue-600">¥{product.selling_price}</div>
                                <div className="text-sm text-gray-500">{getProductUnit(product.category)}</div>
                              </div>
                            </div>
                            
                            <div className="space-y-3 mb-4">
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-medium text-gray-700">制造厂商:</span>
                                <span className="text-gray-900 font-medium">{product.manufacturer}</span>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-medium text-gray-700">规格:</span>
                                <span className="text-gray-900 font-medium">{getSpecificationDisplay(product.category, product.specification)}</span>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-medium text-gray-700">表面处理:</span>
                                <span className="text-gray-900">{getSurfaceDisplayForProduct(product.category, product.surface)}</span>
                              </div>
                            </div>
                            
                            {/* 数量选择和加入购物车 */}
                            <div className="flex items-center gap-2">
                              {/* 数量控制 */}
                              <div className="flex items-center border rounded-lg bg-gray-50">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 hover:bg-gray-200"
                                  onClick={() => setProductQuantity(product.model, getProductQuantity(product.model) - 1)}
                                >
                                  <Minus className="h-3 w-3" />
                                </Button>
                                
                                <input
                                  type="number"
                                  min="1"
                                  max="9999"
                                  value={getProductQuantity(product.model)}
                                  onChange={(e) => {
                                    const value = parseInt(e.target.value) || 1;
                                    setProductQuantity(product.model, value);
                                  }}
                                  className="w-16 text-center text-sm font-medium bg-transparent border-none outline-none"
                                />
                                
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 hover:bg-gray-200"
                                  onClick={() => setProductQuantity(product.model, getProductQuantity(product.model) + 1)}
                                >
                                  <Plus className="h-3 w-3" />
                                </Button>
                              </div>
                              
                              {/* 加入购物车/更新按钮 */}
                              <Button 
                                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                                onClick={() => addToCart(product)}
                                disabled={addingToCart === product.model}
                              >
                                {addingToCart === product.model ? (
                                  <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    {isInCart(product.model) ? "更新中..." : "添加中..."}
                                  </>
                                ) : (
                                  <>
                                    <ShoppingCart className="h-4 w-4 mr-2" />
                                    {isInCart(product.model) ? "更新" : "加入购物车"}
                                  </>
                                )}
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Load More Button */}
                  {products.length < total && !loading && (
                    <div className="flex justify-center mt-8">
                      <Button 
                        onClick={loadMore}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        加载更多 ({products.length}/{total})
                      </Button>
                    </div>
                  )}

                  {/* No Results */}
                  {filteredProducts.length === 0 && !loading && (
                    <div className="text-center py-16">
                      <p className="text-gray-600 text-lg">没有找到符合条件的产品</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>

          {/* Contact Section */}
          <section id="contact" className="container mx-auto px-4 pb-16">
            <div className="bg-white/70 backdrop-blur-xl rounded-3xl p-8 border border-gray-200/50 text-center shadow-xl">
              <h3 className="text-3xl font-bold text-gray-800 mb-6">联系我们</h3>
              <div className="flex flex-col md:flex-row justify-center items-center gap-6 text-gray-700">
                <div className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  <span>400-123-4567</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  <span>陶瓷城</span>
                </div>
              </div>
            </div>
          </section>
        </>
      ) : (
        <UserDashboard onBack={switchToMall} />
      )}

      {/* 备案信息 */}
      <footer className="bg-gray-100 py-6 mt-8">
        <div className="container mx-auto px-4 text-center">
          <div className="flex flex-col md:flex-row justify-center items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <a 
                href="https://beian.miit.gov.cn/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-800"
              >
                蒙ICP备2025026241号
              </a>
            </div>
            <div className="flex items-center gap-2">
              <img 
                src="https://www.beian.gov.cn/img/ghs.png" 
                alt="公安备案图标" 
                className="h-4 w-4"
              />
              <a 
                href="https://www.beian.gov.cn/portal/registerSystemInfo?recordcode=15042902150591" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-800"
              >
                蒙公网安备15042902150591号
              </a>
            </div>
          </div>
        </div>
      </footer>

      <PurchaseDialog
        isOpen={purchaseDialogOpen}
        onClose={() => setPurchaseDialogOpen(false)}
        product={selectedProduct}
      />

      <CartDialog
        isOpen={cartDialogOpen}
        onClose={() => setCartDialogOpen(false)}
      />
      
      {/* 智能客服 */}
      <AIAssistant />
      
      <Toaster />
    </div>
  );
};

export default Index;

