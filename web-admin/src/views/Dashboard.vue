<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="24" :sm="12" :lg="6" v-for="item in statCards" :key="item.title">
        <el-card class="stat-card" :style="{ '--card-color': item.color }">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="28"><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                <animated-number :value="item.value" />
                <span class="stat-unit">{{ item.unit }}</span>
              </div>
              <div class="stat-title">{{ item.title }}</div>
              <div class="stat-trend" :class="item.trend > 0 ? 'up' : 'down'">
                <el-icon><component :is="item.trend > 0 ? 'Top' : 'Bottom'" /></el-icon>
                {{ Math.abs(item.trend) }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <!-- 扫描趋势图 -->
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>扫描趋势</span>
              <el-radio-group v-model="trendPeriod" size="small">
                <el-radio-button label="day">今日</el-radio-button>
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 违规类型分布 -->
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <span>违规类型分布</span>
          </template>
          <div ref="typeChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-row :gutter="20" class="table-row">
      <!-- 最新告警 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新告警</span>
              <el-button link type="primary" @click="viewAllAlerts">
                查看全部 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table :data="latestAlerts" style="width: 100%">
            <el-table-column prop="time" label="时间" width="100">
              <template #default="{ row }">
                <span class="time-text">{{ formatTime(row.time) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="level" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="getAlertType(row.level)" size="small">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleAlert(row)">
                  处理
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 扫描任务 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>扫描任务</span>
              <el-button link type="primary" @click="viewAllTasks">
                查看全部 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table :data="scanTasks" style="width: 100%">
            <el-table-column prop="name" label="任务名称" show-overflow-tooltip />
            <el-table-column prop="progress" label="进度" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.progress" :status="row.status" />
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getTaskType(row.status)" size="small">
                  {{ getTaskStatus(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewTask(row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="quick-actions">
      <template #header>
        <span>快捷操作</span>
      </template>
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6" :md="4" v-for="action in quickActions" :key="action.title">
          <div class="action-item" @click="handleQuickAction(action)">
            <el-icon :size="32" :style="{ color: action.color }">
              <component :is="action.icon" />
            </el-icon>
            <span>{{ action.title }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import { 
  Search, 
  Warning, 
  CircleCheck, 
  Monitor, 
  Top, 
  Bottom, 
  ArrowRight 
} from '@element-plus/icons-vue'

const router = useRouter()

// 图表实例
let trendChartInstance = null
let typeChartInstance = null

// 响应式数据
const trendPeriod = ref('week')
const trendChart = ref(null)
const typeChart = ref(null)

// 统计卡片数据
const statCards = ref([
  {
    title: '今日扫描',
    value: 1234,
    unit: '次',
    icon: 'Search',
    color: '#409eff',
    trend: 12.5
  },
  {
    title: '违规发现',
    value: 56,
    unit: '个',
    icon: 'Warning',
    color: '#e6a23c',
    trend: -8.3
  },
  {
    title: '处理完成',
    value: 48,
    unit: '个',
    icon: 'CircleCheck',
    color: '#67c23a',
    trend: 15.2
  },
  {
    title: '在线服务',
    value: 8,
    unit: '个',
    icon: 'Monitor',
    color: '#909399',
    trend: 0
  }
])

// 最新告警数据
const latestAlerts = ref([
  { id: 1, time: new Date(), level: '高危', content: '检测到未备案网站: example.com' },
  { id: 2, time: new Date(Date.now() - 3600000), level: '中危', content: '发现敏感词汇: 违规内容' },
  { id: 3, time: new Date(Date.now() - 7200000), level: '低危', content: '图片违规: image123.jpg' },
  { id: 4, time: new Date(Date.now() - 10800000), level: '高危', content: 'DDoS攻击检测: 192.168.1.1' },
  { id: 5, time: new Date(Date.now() - 14400000), level: '中危', content: '异常流量: 大量请求来自同一IP' }
])

// 扫描任务数据
const scanTasks = ref([
  { id: 1, name: '全站内容扫描', progress: 100, status: 'success' },
  { id: 2, name: '图片合规检测', progress: 75, status: '' },
  { id: 3, name: '流量异常分析', progress: 45, status: '' },
  { id: 4, name: '备案信息核查', progress: 30, status: 'warning' },
  { id: 5, name: '敏感词检测', progress: 10, status: '' }
])

// 快捷操作
const quickActions = ref([
  { title: '新建扫描', icon: 'Plus', color: '#409eff', action: 'newScan' },
  { title: '查看报表', icon: 'Document', color: '#67c23a', action: 'viewReport' },
  { title: '系统配置', icon: 'Setting', color: '#e6a23c', action: 'systemConfig' },
  { title: '用户管理', icon: 'User', color: '#f56c6c', action: 'userManage' },
  { title: '日志查询', icon: 'Notebook', color: '#909399', action: 'viewLogs' },
  { title: '帮助文档', icon: 'QuestionFilled', color: '#409eff', action: 'viewHelp' }
])

// 初始化趋势图
const initTrendChart = () => {
  if (trendChart.value) {
    trendChartInstance = echarts.init(trendChart.value)
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['扫描次数', '违规发现', '处理完成']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '扫描次数',
          type: 'line',
          smooth: true,
          data: [120, 132, 101, 134, 90, 230, 210],
          itemStyle: { color: '#409eff' }
        },
        {
          name: '违规发现',
          type: 'line',
          smooth: true,
          data: [20, 22, 19, 23, 29, 33, 31],
          itemStyle: { color: '#e6a23c' }
        },
        {
          name: '处理完成',
          type: 'line',
          smooth: true,
          data: [15, 20, 15, 20, 25, 30, 28],
          itemStyle: { color: '#67c23a' }
        }
      ]
    }
    
    trendChartInstance.setOption(option)
  }
}

// 初始化类型分布图
const initTypeChart = () => {
  if (typeChart.value) {
    typeChartInstance = echarts.init(typeChart.value)
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '违规类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: 35, name: '未备案', itemStyle: { color: '#f56c6c' } },
            { value: 30, name: '敏感词', itemStyle: { color: '#e6a23c' } },
            { value: 25, name: '违规图片', itemStyle: { color: '#409eff' } },
            { value: 10, name: '恶意流量', itemStyle: { color: '#67c23a' } }
          ]
        }
      ]
    }
    
    typeChartInstance.setOption(option)
  }
}

// 格式化时间
const formatTime = (time) => {
  const now = new Date()
  const diff = now - time
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (minutes < 1440) {
    return `${Math.floor(minutes / 60)}小时前`
  } else {
    return `${Math.floor(minutes / 1440)}天前`
  }
}

// 获取告警类型
const getAlertType = (level) => {
  const types = {
    '高危': 'danger',
    '中危': 'warning',
    '低危': 'info'
  }
  return types[level] || 'info'
}

// 获取任务类型
const getTaskType = (status) => {
  const types = {
    'success': 'success',
    'warning': 'warning',
    'error': 'danger'
  }
  return types[status] || 'info'
}

// 获取任务状态
const getTaskStatus = (status) => {
  const statusMap = {
    'success': '完成',
    'warning': '警告',
    'error': '失败',
    '': '进行中'
  }
  return statusMap[status] || '进行中'
}

// 处理告警
const handleAlert = (alert) => {
  router.push(`/alert/detail/${alert.id}`)
}

// 查看全部告警
const viewAllAlerts = () => {
  router.push('/alert/list')
}

// 查看任务
const viewTask = (task) => {
  router.push(`/scan/task/${task.id}`)
}

// 查看全部任务
const viewAllTasks = () => {
  router.push('/scan/history')
}

// 处理快捷操作
const handleQuickAction = (action) => {
  const actionMap = {
    newScan: '/scan/new',
    viewReport: '/report/compliance',
    systemConfig: '/config/system',
    userManage: '/user/list',
    viewLogs: '/system/logs',
    viewHelp: '/help'
  }
  
  if (actionMap[action.action]) {
    router.push(actionMap[action.action])
  } else {
    ElMessage.info('功能开发中...')
  }
}

// 处理窗口大小变化
const handleResize = () => {
  trendChartInstance?.resize()
  typeChartInstance?.resize()
}

// 生命周期
onMounted(async () => {
  await nextTick()
  initTrendChart()
  initTypeChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
  typeChartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  .stat-cards {
    margin-bottom: 20px;
    
    .stat-card {
      height: 120px;
      cursor: pointer;
      transition: all 0.3s;
      border-left: 3px solid var(--card-color);
      
      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
      }
      
      .stat-content {
        display: flex;
        align-items: center;
        height: 100%;
        
        .stat-icon {
          width: 60px;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--card-color);
          color: #fff;
          border-radius: 50%;
          margin-right: 20px;
        }
        
        .stat-info {
          flex: 1;
          
          .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 5px;
            
            .stat-unit {
              font-size: 14px;
              color: #909399;
              margin-left: 5px;
            }
          }
          
          .stat-title {
            font-size: 14px;
            color: #606266;
            margin-bottom: 5px;
          }
          
          .stat-trend {
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            
            &.up {
              color: #67c23a;
            }
            
            &.down {
              color: #f56c6c;
            }
            
            .el-icon {
              margin-right: 2px;
            }
          }
        }
      }
    }
  }
  
  .chart-row {
    margin-bottom: 20px;
    
    .chart-card {
      height: 400px;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .chart-container {
        height: 320px;
      }
    }
  }
  
  .table-row {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .time-text {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .quick-actions {
    .action-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      cursor: pointer;
      transition: all 0.3s;
      border-radius: 8px;
      
      &:hover {
        background: #f5f7fa;
        transform: scale(1.05);
      }
      
      span {
        margin-top: 10px;
        font-size: 14px;
        color: #606266;
      }
    }
  }
}
</style>