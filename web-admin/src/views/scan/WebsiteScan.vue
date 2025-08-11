<template>
  <div class="website-scan-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>网站扫描</h1>
      <p>输入网站URL进行内容合规检测扫描</p>
    </div>

    <!-- 扫描配置卡片 -->
    <el-card class="scan-config-card">
      <template #header>
        <div class="card-header">
          <span>扫描配置</span>
          <el-tag type="info" size="small">配置扫描参数</el-tag>
        </div>
      </template>
      
      <el-form :model="scanForm" :rules="scanRules" ref="scanFormRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="网站URL" prop="url" required>
              <el-input
                v-model="scanForm.url"
                placeholder="请输入完整的网站URL，如：https://example.com"
                clearable
                size="large"
              >
                <template #prepend>
                  <el-icon><Globe /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="扫描深度" prop="depth">
              <el-select v-model="scanForm.depth" placeholder="选择扫描深度" size="large">
                <el-option label="浅层扫描 (1-2层)" value="shallow" />
                <el-option label="中层扫描 (3-5层)" value="medium" />
                <el-option label="深层扫描 (5-10层)" value="deep" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="扫描类型" prop="scanTypes">
              <el-checkbox-group v-model="scanForm.scanTypes">
                <el-checkbox label="content" border>内容检测</el-checkbox>
                <el-checkbox label="image" border>图片检测</el-checkbox>
                <el-checkbox label="beian" border>备案检测</el-checkbox>
                <el-checkbox label="security" border>安全检测</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-radio-group v-model="scanForm.priority">
                <el-radio label="low">低</el-radio>
                <el-radio label="normal">普通</el-radio>
                <el-radio label="high">高</el-radio>
                <el-radio label="urgent">紧急</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注" prop="description">
          <el-input
            v-model="scanForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选：添加扫描任务备注信息"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="isScanning"
            @click="startScan"
            :disabled="!scanForm.url"
          >
            <el-icon><Search /></el-icon>
            {{ isScanning ? '扫描中...' : '开始扫描' }}
          </el-button>
          <el-button size="large" @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button size="large" @click="saveTemplate">
            <el-icon><Star /></el-icon>
            保存模板
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 扫描进度卡片 -->
    <el-card v-if="isScanning || scanProgress > 0" class="scan-progress-card">
      <template #header>
        <div class="card-header">
          <span>扫描进度</span>
          <el-tag :type="getProgressTagType()" size="small">
            {{ getProgressStatusText() }}
          </el-tag>
        </div>
      </template>
      
      <div class="progress-content">
        <el-progress
          :percentage="scanProgress"
          :status="getProgressStatus()"
          :stroke-width="20"
          :show-text="false"
        />
        <div class="progress-info">
          <span class="progress-text">{{ scanProgress }}%</span>
          <span class="progress-detail">{{ getProgressDetail() }}</span>
        </div>
        
        <div class="scan-steps">
          <el-steps :active="activeStep" align-center>
            <el-step title="初始化" description="准备扫描环境" />
            <el-step title="连接测试" description="测试网站连通性" />
            <el-step title="内容抓取" description="抓取网页内容" />
            <el-step title="合规检测" description="检测违规内容" />
            <el-step title="生成报告" description="生成扫描报告" />
          </el-steps>
        </div>
        
        <div class="scan-logs">
          <div class="log-header">
            <span>扫描日志</span>
            <el-button link size="small" @click="clearLogs">清空日志</el-button>
          </div>
          <div class="log-content">
            <div
              v-for="(log, index) in scanLogs"
              :key="index"
              class="log-item"
              :class="log.type"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 扫描结果卡片 -->
    <el-card v-if="scanResults.length > 0" class="scan-results-card">
      <template #header>
        <div class="card-header">
          <span>扫描结果</span>
          <div class="result-actions">
            <el-button size="small" @click="exportResults">
              <el-icon><Download /></el-icon>
              导出结果
            </el-button>
            <el-button size="small" @click="viewReport">
              <el-icon><Document /></el-icon>
              查看报告
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="results-summary">
        <el-row :gutter="20">
          <el-col :span="6" v-for="summary in resultsSummary" :key="summary.label">
            <div class="summary-item" :class="summary.type">
              <div class="summary-icon">
                <el-icon :size="24"><component :is="summary.icon" /></el-icon>
              </div>
              <div class="summary-content">
                <div class="summary-value">{{ summary.value }}</div>
                <div class="summary-label">{{ summary.label }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <el-table :data="scanResults" style="width: 100%" max-height="400">
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getViolationType(row.type)" size="small">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="getViolationLevel(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="页面URL" show-overflow-tooltip />
        <el-table-column prop="description" label="违规描述" show-overflow-tooltip />
        <el-table-column prop="timestamp" label="发现时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">
              详情
            </el-button>
            <el-button link type="warning" size="small" @click="handleViolation(row)">
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { 
  Globe, 
  Search, 
  Refresh, 
  Star, 
  Download, 
  Document,
  Warning,
  CircleClose,
  CircleCheck
} from '@element-plus/icons-vue'

const router = useRouter()

// 表单引用
const scanFormRef = ref(null)

// 扫描状态
const isScanning = ref(false)
const scanProgress = ref(0)
const activeStep = ref(0)
const scanLogs = ref([])
const scanResults = ref([])

// 扫描表单
const scanForm = reactive({
  url: '',
  depth: 'medium',
  scanTypes: ['content', 'image', 'beian'],
  priority: 'normal',
  description: ''
})

// 表单验证规则
const scanRules = {
  url: [
    { required: true, message: '请输入网站URL', trigger: 'blur' },
    { 
      pattern: /^https?:\/\/.+/,
      message: '请输入有效的网站URL，以http://或https://开头',
      trigger: 'blur'
    }
  ],
  scanTypes: [
    { required: true, message: '请选择至少一种扫描类型', trigger: 'change' }
  ]
}

// 结果摘要
const resultsSummary = computed(() => [
  {
    label: '总页面数',
    value: scanResults.value.length,
    icon: 'Document',
    type: 'info'
  },
  {
    label: '违规页面',
    value: scanResults.value.filter(r => r.level === 'high' || r.level === 'medium').length,
    icon: 'Warning',
    type: 'warning'
  },
  {
    label: '高危违规',
    value: scanResults.value.filter(r => r.level === 'high').length,
    icon: 'CircleClose',
    type: 'danger'
  },
  {
    label: '已处理',
    value: scanResults.value.filter(r => r.handled).length,
    icon: 'CircleCheck',
    type: 'success'
  }
])

// 开始扫描
const startScan = async () => {
  try {
    await scanFormRef.value.validate()
    
    isScanning.value = true
    scanProgress.value = 0
    activeStep.value = 0
    scanLogs.value = []
    scanResults.value = []
    
    addLog('info', '开始扫描任务...')
    
    // 模拟扫描过程
    await simulateScan()
    
    ElMessage.success('扫描完成！')
  } catch (error) {
    ElMessage.error('表单验证失败，请检查输入')
  }
}

// 模拟扫描过程
const simulateScan = async () => {
  const steps = [
    { step: 1, progress: 20, message: '初始化扫描环境...' },
    { step: 2, progress: 40, message: '测试网站连通性...' },
    { step: 3, progress: 60, message: '抓取网页内容...' },
    { step: 4, progress: 80, message: '检测违规内容...' },
    { step: 5, progress: 100, message: '生成扫描报告...' }
  ]
  
  for (const step of steps) {
    activeStep.value = step.step - 1
    scanProgress.value = step.progress
    addLog('info', step.message)
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  // 生成模拟结果
  generateMockResults()
  isScanning.value = false
}

// 添加日志
const addLog = (type, message) => {
  const time = new Date().toLocaleTimeString()
  scanLogs.value.push({ type, message, time })
}

// 生成模拟结果
const generateMockResults = () => {
  const mockResults = [
    {
      type: '未备案',
      level: 'high',
      url: 'https://example.com/page1',
      description: '该网站未在工信部备案，存在合规风险',
      timestamp: new Date(),
      handled: false
    },
    {
      type: '敏感词',
      level: 'medium',
      url: 'https://example.com/page2',
      description: '页面内容包含敏感词汇，需要人工审核',
      timestamp: new Date(),
      handled: false
    },
    {
      type: '违规图片',
      level: 'low',
      url: 'https://example.com/page3',
      description: '页面包含可能违规的图片内容',
      timestamp: new Date(),
      handled: true
    }
  ]
  
  scanResults.value = mockResults
  addLog('success', `扫描完成，发现 ${mockResults.length} 个问题`)
}

// 重置表单
const resetForm = () => {
  scanFormRef.value?.resetFields()
  scanForm.url = ''
  scanForm.depth = 'medium'
  scanForm.scanTypes = ['content', 'image', 'beian']
  scanForm.priority = 'normal'
  scanForm.description = ''
}

// 保存模板
const saveTemplate = () => {
  ElMessage.info('模板保存功能开发中...')
}

// 清空日志
const clearLogs = () => {
  scanLogs.value = []
}

// 导出结果
const exportResults = () => {
  ElMessage.info('导出功能开发中...')
}

// 查看报告
const viewReport = () => {
  ElMessage.info('报告查看功能开发中...')
}

// 查看详情
const viewDetail = (row) => {
  ElMessage.info(`查看详情：${row.url}`)
}

// 处理违规
const handleViolation = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要处理这个违规问题吗？\n类型：${row.type}\n级别：${row.level}`,
      '处理违规',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    row.handled = true
    ElMessage.success('违规问题已标记为已处理')
  } catch {
    // 用户取消
  }
}

// 获取进度状态
const getProgressStatus = () => {
  if (scanProgress.value === 100) return 'success'
  if (scanProgress.value > 50) return 'warning'
  return ''
}

// 获取进度标签类型
const getProgressTagType = () => {
  if (scanProgress.value === 100) return 'success'
  if (scanProgress.value > 50) return 'warning'
  return 'info'
}

// 获取进度状态文本
const getProgressStatusText = () => {
  if (scanProgress.value === 100) return '扫描完成'
  if (scanProgress.value > 0) return '扫描中'
  return '等待开始'
}

// 获取进度详情
const getProgressDetail = () => {
  if (scanProgress.value === 100) return '扫描任务已完成'
  if (scanProgress.value > 50) return '正在检测违规内容'
  if (scanProgress.value > 20) return '正在抓取网页内容'
  return '正在初始化...'
}

// 获取违规类型标签类型
const getViolationType = (type) => {
  const typeMap = {
    '未备案': 'danger',
    '敏感词': 'warning',
    '违规图片': 'info',
    '安全漏洞': 'error'
  }
  return typeMap[type] || 'info'
}

// 获取违规级别标签类型
const getViolationLevel = (level) => {
  const levelMap = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return levelMap[level] || 'info'
}

// 格式化时间
const formatTime = (time) => {
  return new Date(time).toLocaleString()
}

// 生命周期
onMounted(() => {
  // 页面初始化
})
</script>

<style lang="scss" scoped>
.website-scan-container {
  .page-header {
    margin-bottom: 20px;
    
    h1 {
      color: #303133;
      margin-bottom: 8px;
      font-size: 24px;
      font-weight: 600;
    }
    
    p {
      color: #909399;
      font-size: 14px;
      margin: 0;
    }
  }
  
  .scan-config-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  .scan-progress-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .progress-content {
      .progress-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 20px 0;
        
        .progress-text {
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
        
        .progress-detail {
          color: #909399;
          font-size: 14px;
        }
      }
      
      .scan-steps {
        margin: 30px 0;
      }
      
      .scan-logs {
        margin-top: 20px;
        
        .log-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
          
          span {
            font-weight: 600;
            color: #303133;
          }
        }
        
        .log-content {
          max-height: 200px;
          overflow-y: auto;
          border: 1px solid #ebeef5;
          border-radius: 4px;
          padding: 10px;
          background: #fafafa;
          
          .log-item {
            display: flex;
            margin-bottom: 8px;
            font-size: 12px;
            
            .log-time {
              color: #909399;
              margin-right: 10px;
              min-width: 80px;
            }
            
            .log-message {
              color: #606266;
            }
            
            &.info .log-message {
              color: #409eff;
            }
            
            &.success .log-message {
              color: #67c23a;
            }
            
            &.warning .log-message {
              color: #e6a23c;
            }
            
            &.error .log-message {
              color: #f56c6c;
            }
          }
        }
      }
    }
  }
  
  .scan-results-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .result-actions {
        display: flex;
        gap: 10px;
      }
    }
    
    .results-summary {
      margin-bottom: 20px;
      
      .summary-item {
        display: flex;
        align-items: center;
        padding: 20px;
        border-radius: 8px;
        background: #f5f7fa;
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .summary-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          margin-right: 16px;
          color: #fff;
        }
        
        .summary-content {
          .summary-value {
            font-size: 24px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .summary-label {
            font-size: 14px;
            color: #909399;
          }
        }
        
        &.info .summary-icon {
          background: #409eff;
        }
        
        &.warning .summary-icon {
          background: #e6a23c;
        }
        
        &.danger .summary-icon {
          background: #f56c6c;
        }
        
        &.success .summary-icon {
          background: #67c23a;
        }
      }
    }
  }
}
</style> 