<script setup lang="ts">
import { ref, onMounted, nextTick, watch, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { fetchSalesTrend, fetchTopProducts } from '@/api/sales';
import { useRoute } from 'vue-router';

// 获取当前路由
const route = useRoute();

// 数据定义
const salesData = ref<{ dates: string[]; salesValues: number[]; amounts: number[] }>({ dates: [], salesValues: [], amounts: [] });
const topProducts = ref<{ model: string; amount: number; }[]>([]);

// 引用图表和表格容器DOM元素
const salesChartRef = ref<HTMLElement | null>(null);
const productCardRef = ref<HTMLElement | null>(null);
const tableContainerRef = ref<HTMLElement | null>(null);
let salesChart: echarts.ECharts | null = null;

// 计算表格高度
const tableHeight = ref(300);

// 获取销售趋势数据
const fetchSalesData = async () => {
  try {
    const currentDate = new Date();
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    const length = 12;

    const response = await fetchSalesTrend(year, month, length);
    if (response.data.code === 200) {
      const apiData = response.data.data;
      
      // 生成对应的日期数组（根据后端YearMonthUtil的逻辑）
      const dates = generateDateLabels(year, month, length);
      
      // 提取后端返回的数据，注意字段名匹配，并处理null值
      const salesValues = apiData.map((item: any) => item ? (item.total_amount || 0) : 0); // 销量
      const amounts = apiData.map((item: any) => item ? (item.total_price || 0) : 0); // 销售金额

      // 反转数组顺序，使图表从左到右按时间顺序显示（早期在左，最新在右）
      salesData.value = {
        dates: dates.reverse(),
        salesValues: salesValues.reverse(), 
        amounts: amounts.reverse()
      };
      
    } else {
      salesData.value = {
        dates: [],
        salesValues: [],
        amounts: []
      };
    }
  } catch (error) {
    console.error('获取销售趋势数据失败：', error);
    salesData.value = {
      dates: [],
      salesValues: [],
      amounts: []
    };
  }
};

// 生成日期标签（模拟后端YearMonthUtil的逻辑）
const generateDateLabels = (year: number, month: number, length: number): string[] => {
  const dates: string[] = [];
  let currentYear = year;
  let currentMonth = month;
  
  for (let i = 0; i < length; i++) {
    const monthStr = currentMonth < 10 ? `0${currentMonth}` : `${currentMonth}`;
    dates.push(`${currentYear}-${monthStr}`); // 按顺序添加，第一个是本月
    
    currentMonth--;
    if (currentMonth <= 0) {
      currentMonth = 12;
      currentYear--;
    }
  }
  
  return dates;
};

// 获取最火爆卖品数据
const fetchTopProductsData = async () => {
  try {
    const response = await fetchTopProducts();
    if (response.data.code === 200) {
      topProducts.value = response.data.data;
    } else {
      topProducts.value = [];
    }
  } catch (error) {
    console.error('获取最火爆卖品数据失败：', error);
    topProducts.value = [];
  }
};

// 初始化销售趋势图表
const initSalesChart = () => {
  if (!salesChartRef.value) return;

  if (salesChart) {
    salesChart.dispose();
  }

  salesChart = echarts.init(salesChartRef.value);
  const option = {
    title: { text: '销售趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['销量', '销售金额'], top: '5%' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: salesData.value.dates,
      axisLabel: {
        interval: 0,
        rotate: salesData.value.dates.length > 5 ? 30 : 0
      }
    },
    yAxis: [
      { type: 'value', name: '销量', position: 'left' },
      { type: 'value', name: '销售金额（元）', position: 'right', axisLabel: { formatter: '{value}' } }
    ],
    series: [
      {
        name: '销量',
        type: 'line',
        data: salesData.value.salesValues,
        smooth: true,
        yAxisIndex: 0,
        lineStyle: { color: '#409EFF' },
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '销售金额',
        type: 'line',
        data: salesData.value.amounts,
        smooth: true,
        yAxisIndex: 1,
        lineStyle: { color: '#67C23A' },
        itemStyle: { color: '#67C23A' }
      }
    ]
  };
  salesChart.setOption(option);
};

// 更新表格高度
const updateTableHeight = () => {
  if (!productCardRef.value || !tableContainerRef.value) return;

  const cardPadding = 20;
  const titleHeight = 40;

  const cardHeight = productCardRef.value.clientHeight;
  const availableHeight = cardHeight - titleHeight - cardPadding;

  tableHeight.value = Math.max(availableHeight, 200);
  tableContainerRef.value.style.height = `${tableHeight.value}px`;
};

// 处理窗口大小变化和缩放
const handleResize = () => {
  setTimeout(() => {
    if (salesChart) {
      salesChart.resize();
    }
    updateTableHeight();
  }, 200);
};

// 监听路由变化
watch(
    () => route.path,
    (newPath) => {
      if (newPath.includes(route.name as string)) {
        nextTick(() => {
          handleResize();
        });
      }
    }
);

// 监听销售数据变化，重新渲染图表
watch(
  () => salesData.value,
  (newData) => {
    if (newData.dates.length > 0) {
      nextTick(() => {
        initSalesChart();
      });
    }
  },
  { deep: true }
);

// 加载所有数据
const loadAllData = async () => {
  await fetchSalesData();
  await fetchTopProductsData();

  await nextTick();
  initSalesChart();
  updateTableHeight();
};

onMounted(async () => {
  await loadAllData();

  window.addEventListener('resize', handleResize);

  const observer = new MutationObserver(handleResize);
  observer.observe(document.body, {
    attributes: true,
    childList: true,
    subtree: true
  });

  (window as any).__resizeObserver = observer;
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if ((window as any).__resizeObserver) {
    (window as any).__resizeObserver.disconnect();
    (window as any).__resizeObserver = null;
  }

  if (salesChart) {
    salesChart.dispose();
    salesChart = null;
  }
});
</script>


<template>
  <div class="welcome-container">
    <h1>欢迎来到万邦陶瓷库存管理系统</h1>
    <hr />



    <!-- 图表部分 -->
    <el-row :gutter="20" class="charts-section">
      <!-- 销售趋势图 -->
      <el-col :span="18">
        <el-card shadow="hover" class="rounded-card chart-card">
          <section ref="salesChartRef" class="sales-chart"></section>
        </el-card>
      </el-col>

      <!-- 最火爆卖品表格 -->
      <el-col :span="6">
        <el-card shadow="hover" ref="productCardRef" class="rounded-card product-card">
          <div class="card-header">
            <h3>最火爆卖品</h3>
          </div>
          <div ref="tableContainerRef" class="table-container">
            <el-table
                :data="topProducts"
                border
                style="width: 100%"
                size="small"
                :height="tableHeight"
                :header-cell-style="{
                background: '#f5f7fa',
                color: '#606266',
                fontWeight: 'bold'
              }">
              <el-table-column
                  prop="model"
                  label="产品型号"
                  min-width="70"
                  show-overflow-tooltip />
              <el-table-column
                  prop="amount"
                  label="销量"
                  min-width="50"
                  width="70"
                  align="center" />
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>


<style scoped>
/* 样式保持不变 */
.welcome-container {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.charts-section {
  display: flex;
  height: calc(100% - 80px);
  min-height: 500px;
}

.el-row {
  width: 100%;
}

.chart-card,
.product-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.card-header {
  flex: 0 0 auto;
  padding-bottom: 10px;
}

.table-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  min-height: 200px;
}

.sales-chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
  flex: 1;
}

h1 {
  text-align: center;
  color: #409EFF;
  margin-top: 0;
  margin-bottom: 15px;
}

h3 {
  text-align: center;
  margin: 0 0 10px 0;
}



/* 添加圆角样式 */
.rounded-card {
  border-radius: 15px;
  overflow: hidden;
}

/* 确保在小屏幕上表格不会太小 */
@media screen and (max-width: 1400px) {
  .charts-section {
    min-height: 450px;
  }
}

/* 适应不同缩放级别 */
@media screen and (min-resolution: 120dpi) {
  .table-container {
    overflow: auto;
  }

  .product-card {
    overflow: visible;
  }
}
</style>