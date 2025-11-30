// 通用响应结构
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// 分页响应数据
export interface PaginationData<T> {
  total: number;
  current: number;
  size: number;
  records: T[];
}

// 分页查询参数
export interface PaginationParams {
  current?: number;
  size?: number;
}

// 用户登录请求参数
export interface LoginRequest {
  username: string;
  password: string;
}

// 用户登录响应数据
export interface UserLoginResp {
  id: number;
  username: string;
  avatar: string;
  phone: string;
  email?: string;
  role_id: number;
}

// 用户注册请求参数
export interface RegisterRequest {
  username: string;
  password: string;
  phone: string;
}

// 重置密码请求参数
export interface ResetPasswordRequest {
  username: string;
  phone: string;
  new_password: string;
}

// 用户修改信息请求参数
export interface UserChangeInfoReq {
  username?: string;
  password?: string; // 旧密码
  new_password?: string; // 新密码
  phone?: string;
  avatar?: string;
  email?: string;
}

// 用户列表项
export interface UserListItem {
  id: number;
  username: string;
  phone: string;
  role_id: number;
}

// 库存商品项
export interface InventoryItem {
  id: number;
  model: string;
  manufacturer: string;
  specification: string;
  surface: number; // 1=抛光, 2=哑光, 3=釉面, 4=通体大理石, 5=微晶石, 6=岩板
  category: number; // 1=墙砖, 2=地砖
  warehouse_num: number;
  total_amount: number;
  unit_per_box: number;
  selling_price?: number;
  picture?: string; // 商品图片URL
  remark?: string;
  version?: number;
  create_time?: string;
  update_time?: string;
}

// 库存查询参数
export interface InventoryQueryParams extends PaginationParams {
  category?: string;
  surface?: string;
}

// 库存修改请求参数
export interface ItemsChangeReq {
  id: number;
  model: string;
  manufacturer: string;
  specification: string;
  surface: number;
  category: number;
  warehouse_num: number;
  total_amount: number;
  unit_per_box: number;
  selling_price?: number;
  picture?: string;
  remark?: string;
}

// 根据型号获取库存响应
export interface ItemsFetchResp {
  id: number;
  total_amount: number;
}

// 日志记录项 
export interface LogRecord {
  id: number;
  item_id: number;
  log_type: number; // 1=入库 2=出库 3=调拨 4=冲正
  amount_change: number;
  source_warehouse?: number;
  target_warehouse?: number;
  remark?: string;
  create_time?: string;
  update_time?: string;
}

// 日志查询参数
export interface LogsQueryParams extends PaginationParams {
  log_type?: number;
  start_time?: string;
  end_time?: string;
}

// 日志修改请求参数
export interface LogsChangeReq {
  id: number;
  item_id: number;
  log_type: number;
  source_warehouse?: number;
  target_warehouse?: number;
  amount_change: number;
  remark?: string;
}

// 入库记录请求参数
export interface LogsInboundReq {
  model: string;
  manufacturer: string;
  specification: string;
  warehouse_num: number;
  selling_price: number;
  picture?: string;
  category: number;
  surface: number;
  total_amount: number;
  unit_per_box: number;
  remark?: string;
}

// 调拨记录请求参数
export interface LogsTransferReq {
  item_id: number;
  log_type: number;
  source_warehouse: number;
  target_warehouse: number;
  remark?: string;
}

// 销售统计项
export interface SalesItem {
  model: string;
  amount: number;
}

// 销售趋势响应项
export interface SalesTrendResp {
  model: string;
  amount: number;
}

// 订单项
export interface OrderItem {
  item_id: number;
  model: string;
  amount: number;
  subtotal_price: number;
}

// 新建订单请求参数
export interface OrderNewReq {
  customer_phone: string;
  total_price: number;
  items: OrderItem[];
  remark?: string;
}

// 订单列表项
export interface OrderListItem {
  id: number;
  order_no: string;
  customer_phone: string;
  total_price: number;
  dispatch_status: number; // 0=未派送 1=已派送
  remark?: string;
  create_time?: string;
  update_time?: string;
  sub_order_count: number;
}

// Order类型 - 用于列表和详情
export interface Order extends OrderListItem {
  operator_id?: number;
  operator_name?: string;
  adjusted_amount?: number | null;
  aftersale_status?: number;
  delivery_address?: string;
  sub_order?: SubOrderItem[]; // 订单详情中包含的子订单项
}

// 订单查询参数
export interface OrderQueryParams extends PaginationParams {
  start_time?: string;
  end_time?: string;
  customer_phone?: string;
}

// 子订单项
export interface SubOrderItem {
  id: number;
  order_id: number;
  item_id: number;
  amount: number;
  subtotal_price: number;
  create_time?: string;
  update_time?: string;
  // 扩展字段 - 用于订单详情显示
  model_number?: string;
  specification?: string;
  manufacturer?: string;
  quantity?: number;
  adjusted_quantity?: number;
  price_per_piece?: number;
  subtotal?: number;
}

// 订单详情响应
export interface OrderDetailResp {
  id: number;
  order_no: string;
  customer_phone: string;
  total_price: number;
  create_time?: string;
  update_time?: string;
  sub_order: SubOrderItem[];
  remark?: string;
}

// 订单修改请求参数
export interface OrderChangeReq {
  id: number;
  customer_phone: string;
  remark?: string;
}

// 子订单修改请求参数
export interface OrderSubChangeReq {
  id: number; // 子订单项ID
  order_id?: number; // 母订单ID，新增时需要
  item_id?: number; // 商品ID，新增时需要
  amount: number;
  subtotal_price: number;
  change_type: number; // 0=修改, 1=新增, 2=删除
}

// 订单派送请求参数
export interface OrderDispatchReq {
  id: number;
  customer_phone: string;
  delivery_address: string;
  order_no: string;
  delivery_fee: number;
  goods_weight: number;
  remark?: string;
}

// 司机信息
export interface Driver {
  id: number;
  name: string;
  phone: string;
  avatar?: string;
  audit_status: number; // 0=待审核 1=已通过 2=已拒绝
  work_status: number; // 1=空闲 2=忙碌 3=离线
  openid?: string;
  money: number;
  create_time?: string; // 统一使用蛇形命名
  update_time?: string; // 统一使用蛇形命名
}

// 司机登录请求参数
export interface DriverLoginReq {
  code: string;
  phone: string;
}

// 司机登录响应数据
export interface DriverLoginResp {
  id: number;
  name: string;
  phone: string;
  avatar?: string;
  audit_status: number;
  work_status: number;
  money: number;
  token: string;
}

// 路线规划响应数据
export interface RouteResp {
  distance: number;
  duration: number;
  polyline: number[][];
}

// 派送订单项
export interface DispatchOrderItem {
  id: number;
  order_no: string;
  driver_id?: number;
  delivery_address: string;
  delivery_fee: number;
  goods_weight?: number; // 可选，因为接口文档显示可能为null
  remark?: string;
  create_time?: string;
  update_time?: string;
  dispatch_status: number; // 统一使用蛇形命名
}

// 派送订单查询参数
export interface DispatchOrderQueryParams extends PaginationParams {
  // 根据需要添加其他查询参数
}

// 可用订单项
export interface AvailableOrderItem {
  order_no: string;
  customer_phone: string;
  delivery_address: string;
  delivery_fee: number;
  goods_weight: number;
  remark?: string;
}

// 司机位置更新请求参数
export interface DriverLocationUpdateReq {
  id: number;
  latitude: number; // 对应后端BigDecimal类型
  longitude: number; // 对应后端BigDecimal类型
}

// 抢单请求参数
export interface RobOrderReq {
  id: number; // 对应后端Integer类型
  order_no: string;
}

// 通用操作响应（如抢单成功）
export interface OperationResp {
  success: boolean;
}

// 兼容旧版接口的类型定义，保持向后兼容
export interface DeliveryQueryParams extends PaginationParams {
  order_no?: string;
  customer_phone?: string;
  status?: number;
  driver_id?: number;
}

export interface DeliveryOrder {
  id?: number;
  order_no: string;
  driver_id?: number;
  driver_name?: string;
  driver_phone?: string;
  customer_phone: string;
  delivery_address: string;
  delivery_status: number;
  delivery_fee: number;
  delivery_note?: string;
  goods_weight: number;
  create_time?: string;
  update_time?: string;
}

export interface DispatchRequest {
  order_id: number;
  order_no: string;
  customer_phone: string;
  delivery_address: string;
  delivery_note?: string;
  goods_weight: number;
  delivery_fee: number;
}

// 司机列表响应数据 (特殊格式，只有total和records)
export interface DriverListData {
  total: number;
  records: Driver[];
}

// 兼容旧版本的日志记录接口（用于已有页面）
export interface InventoryLog {
  id?: number;
  inventory_item_id: number;
  operation_type: number; // 前端使用的字段名
  quantity_change: number; // 前端使用的字段名
  operator_id?: number;
  source_warehouse?: number | null;
  target_warehouse?: number | null;
  remark?: string;
  create_time?: string;
  update_time?: string;
}

// 日志查询参数（兼容版本）
export interface LogQueryParams extends PaginationParams {
  operation_type?: number;
  start_time?: string;
  end_time?: string;
  sort?: string;
  order?: string;
}

// 日志修改请求（兼容版本）
export interface InventoryLogChangeRequest {
  id: number;
  inventory_item_id: number;
  operation_type: number;
  quantity_change: number;
  operator_id: number;
  source_warehouse?: number | null;
  target_warehouse?: number | null;
  remark?: string;
}

// 选品单相关接口定义
export interface SelectionListItem {
  id: number;
  selection_no: string;
  customer_phone?: string;
  status: number; // 0=待跟进, 1=已联系, 2=已到店, 3=已失效
  delivery_address?: string;
  remark?: string;
  create_time: string;
  update_time: string;
}

export interface SelectionListQueryParams extends PaginationParams {
  selection_no?: string;
  customer_phone?: string;
  status?: number;
}

export interface SelectionItemRecord {
  id?: number; // 注意：根据API文档，详情接口可能不返回此字段
  item_model: string;
  item_specification?: string;
  item_selling_price: number;
  amount: number;
}

export interface SelectionListChangeReq {
  customer_phone?: string;
  delivery_address?: string;
  remark?: string;
}

export interface SelectionItemAddReq {
  item_model: string;
  item_selling_price: number;
  amount: number;
}

// 司机查询参数
export interface DriverQueryParams extends PaginationParams {
  name?: string;
  phone?: string;
  audit_status?: number;
  work_status?: number;
}

// 司机审核请求参数
export interface DriverApprovalRequest {
  id: number;
  audit_status: number; // 1=通过, 2=拒绝
  remark?: string;
}

// 订单商品项操作相关
export interface OrderItemRequest {
  order_id: number;
  item_id: number;
  amount: number;
  subtotal_price: number;
}

// 扩展用户信息（包含角色key）
export interface ExtendedUserInfo extends UserLoginResp {
  role_key?: string;
}