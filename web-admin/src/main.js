import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// 样式导入
import 'element-plus/dist/index.css'
import '@/styles/index.scss'

// 进度条
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置进度条
NProgress.configure({ showSpinner: false })

const app = createApp(App)

// 使用插件
app.use(createPinia())
app.use(router)

// 配置 Element Plus - 确保正确配置
app.use(ElementPlus, {
  locale: zhCn,
  size: 'default'
})

// 注册所有Element Plus图标（在app创建和插件注册后）
try {
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
  console.log('Element Plus图标注册成功')
} catch (error) {
  console.warn('Element Plus图标注册失败:', error)
}

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误捕获:', err, info)
  
  // 避免在错误处理中再次调用ElMessage
  if (err && err.message && !err.message.includes('ElMessage')) {
    console.error('应用错误:', err.message)
  }
  
  // 处理表单验证错误
  if (err && err.message && err.message.includes('validate is not a function')) {
    console.warn('表单验证方法未找到，可能是Element Plus版本兼容性问题')
  }
}

// 挂载应用
app.mount('#app')

// 移除加载动画
document.getElementById('loading-app')?.remove()

console.log('应用启动完成')