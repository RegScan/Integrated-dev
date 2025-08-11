<template>
  <div class="login-container">
    <div class="login-background">
      <div class="bg-shape bg-shape-1"></div>
      <div class="bg-shape bg-shape-2"></div>
      <div class="bg-shape bg-shape-3"></div>
    </div>
    
    <el-card class="login-card">
      <div class="login-header">
        <img src="/logo.svg" alt="Logo" class="login-logo" />
        <h2 class="login-title">内容合规检测系统</h2>
        <p class="login-subtitle">Content Compliance Detection System</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            clearable
            class="login-input"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            clearable
            class="login-input"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="captcha" v-if="showCaptcha">
          <div class="captcha-container">
            <el-input
              v-model="loginForm.captcha"
              placeholder="请输入验证码"
              size="large"
              clearable
              class="captcha-input"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
            <div class="captcha-image" @click="refreshCaptcha">
              <img :src="captchaUrl" alt="验证码" />
            </div>
          </div>
        </el-form-item>
        
        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" @click="handleForgotPassword">忘记密码？</el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <div class="login-footer">
            <span>还没有账号？</span>
            <el-link type="primary" @click="handleRegister">立即注册</el-link>
          </div>
        </el-form-item>
      </el-form>
      
      <el-divider content-position="center">快速登录</el-divider>
      
      <div class="social-login">
        <el-tooltip content="微信登录" placement="bottom">
          <div class="social-icon" @click="handleSocialLogin('wechat')">
            <el-icon :size="24">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path fill="currentColor" d="M174.72 855.68l135.296-45.12 23.68 11.84C388.096 849.536 448.576 864 512 864c211.84 0 384-166.784 384-352S723.84 160 512 160 128 326.784 128 512c0 69.12 24.96 139.264 70.848 199.232l22.08 28.8-46.272 115.584zm-45.248 82.56A32 32 0 0 1 89.6 896l58.368-145.92C94.72 680.32 64 596.864 64 512 64 299.904 256 96 512 96s448 203.904 448 416-192 416-448 416a461.06 461.06 0 0 1-206.912-48.384l-175.616 58.56z"/>
                <path fill="currentColor" d="M512 563.2a51.2 51.2 0 1 1 0-102.4 51.2 51.2 0 0 1 0 102.4m192 0a51.2 51.2 0 1 1 0-102.4 51.2 51.2 0 0 1 0 102.4m-384 0a51.2 51.2 0 1 1 0-102.4 51.2 51.2 0 0 1 0 102.4"/>
              </svg>
            </el-icon>
          </div>
        </el-tooltip>
        <el-tooltip content="GitHub登录" placement="bottom">
          <div class="social-icon" @click="handleSocialLogin('github')">
            <el-icon :size="24">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path fill="currentColor" d="M715.648 625.152L670.4 579.904l90.496-90.56c75.008-74.944 85.12-186.368 22.656-248.896-62.528-62.464-173.952-52.352-248.96 22.656L444.16 353.6l-45.248-45.248 90.496-90.496c100.032-99.968 251.968-110.08 339.456-22.656 87.488 87.488 77.312 239.424-22.656 339.456l-90.496 90.496zm-90.496 90.496l-90.496 90.496C434.624 906.112 282.688 916.224 195.2 828.8c-87.488-87.488-77.312-239.424 22.656-339.456l90.496-90.496 45.248 45.248-90.496 90.56c-75.008 74.944-85.12 186.368-22.656 248.896 62.528 62.464 173.952 52.352 248.96-22.656l90.496-90.496zm0-362.048l45.248 45.248L398.848 670.4 353.6 625.152z"/>
              </svg>
            </el-icon>
          </div>
        </el-tooltip>
        <el-tooltip content="钉钉登录" placement="bottom">
          <div class="social-icon" @click="handleSocialLogin('dingtalk')">
            <el-icon :size="24">
              <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path fill="currentColor" d="M79.36 432.256L591.744 944.64a32 32 0 0 0 35.2 6.784l253.44-108.544a32 32 0 0 0 9.984-52.032l-153.856-153.92a32 32 0 0 0-36.928-6.016l-69.888 34.944L358.08 394.24l35.008-69.888a32 32 0 0 0-5.952-36.928L233.152 133.568a32 32 0 0 0-52.032 10.048L72.512 397.056a32 32 0 0 0 6.784 35.2zm60.48-29.952l81.536-190.08L325.568 316.48l-24.64 49.216-20.608 41.216 32.576 32.64 271.552 271.552 32.64 32.64 41.216-20.672 49.28-24.576 104.192 104.128-190.08 81.472zM512 320v-64a256 256 0 0 1 256 256h-64a192 192 0 0 0-192-192m0-192V64a448 448 0 0 1 448 448h-64a384 384 0 0 0-384-384"/>
              </svg>
            </el-icon>
          </div>
        </el-tooltip>
      </div>
    </el-card>
    
    <div class="login-copyright">
      <p>&copy; 2024 内容合规检测系统 版权所有</p>
      <p>
        <el-link type="info" @click="handleTerms">服务条款</el-link>
        <el-divider direction="vertical" />
        <el-link type="info" @click="handlePrivacy">隐私政策</el-link>
        <el-divider direction="vertical" />
        <el-link type="info" @click="handleHelp">帮助中心</el-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
// 使用更简单的图标导入方式
import { 
  User, 
  Lock, 
  Key
} from '@element-plus/icons-vue'
import userController from '@/controllers/UserController'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 表单引用 - 明确指定类型
const loginFormRef = ref()

// 响应式数据
const loading = ref(false)
const showCaptcha = ref(false)
const rememberMe = ref(false)
const captchaUrl = ref('/api/captcha?t=' + Date.now())

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  captcha: ''
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 4, message: '验证码长度为 4 个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  console.log('开始登录处理...')
  console.log('表单引用:', loginFormRef.value)
  
  // 检查表单引用是否存在
  if (!loginFormRef.value) {
    console.error('表单引用未找到')
    ElMessage.error('表单初始化失败，请刷新页面重试')
    return
  }
  
  // 检查表单数据
  if (!loginForm.username.trim()) {
    ElMessage.error('请输入用户名')
    return
  }
  
  if (!loginForm.password) {
    ElMessage.error('请输入密码')
    return
  }
  
  if (showCaptcha.value && !loginForm.captcha) {
    ElMessage.error('请输入验证码')
    return
  }
  
  loading.value = true
  
  try {
    console.log('调用登录API...')
    await userController.login(loginForm.username, loginForm.password)
    
    // 记住我
    if (rememberMe.value) {
      localStorage.setItem('rememberUsername', loginForm.username)
    } else {
      localStorage.removeItem('rememberUsername')
    }
    
    // 跳转到目标页面
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
    
    ElMessage.success('登录成功，欢迎回来！')
  } catch (error) {
    console.error('登录失败:', error)
    
    // 登录失败次数过多，显示验证码
    if (error.response?.data?.needCaptcha) {
      showCaptcha.value = true
      refreshCaptcha()
    }
    
    // 显示错误信息
    const errorMessage = error.response?.data?.message || error.message || '登录失败，请检查用户名和密码'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

// 刷新验证码
const refreshCaptcha = () => {
  captchaUrl.value = '/api/captcha?t=' + Date.now()
}

// 忘记密码
const handleForgotPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}

// 注册
const handleRegister = () => {
  router.push('/register')
}

// 社交登录
const handleSocialLogin = (type) => {
  ElMessage.info(`${type}登录功能开发中...`)
}

// 服务条款
const handleTerms = () => {
  window.open('/terms', '_blank')
}

// 隐私政策
const handlePrivacy = () => {
  window.open('/privacy', '_blank')
}

// 帮助中心
const handleHelp = () => {
  window.open('/help', '_blank')
}

// 生命周期
onMounted(async () => {
  console.log('Login 组件挂载开始...')
  
  // 等待 DOM 更新完成
  await nextTick()
  console.log('DOM 更新完成')
  
  // 检查表单引用
  console.log('表单引用状态:', {
    exists: !!loginFormRef.value,
    type: typeof loginFormRef.value,
    methods: loginFormRef.value ? Object.getOwnPropertyNames(loginFormRef.value) : 'N/A'
  })
  
  // 自动填充记住的用户名
  const rememberedUsername = localStorage.getItem('rememberUsername')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    rememberMe.value = true
  }
  
  // 开发环境自动填充
  if (import.meta.env.DEV) {
    loginForm.username = 'admin'
    loginForm.password = '123456'
    console.log('开发环境自动填充完成')
  }
  
  // 验证表单引用是否正确初始化
  if (loginFormRef.value) {
    console.log('表单引用初始化成功')
    // 检查是否有 validate 方法
    if (typeof loginFormRef.value.validate === 'function') {
      console.log('Element Plus 表单验证方法可用')
    } else {
      console.warn('Element Plus 表单验证方法不可用，使用手动验证')
    }
  } else {
    console.error('表单引用初始化失败')
  }
  
  console.log('Login 组件挂载完成')
})
</script>

<style lang="scss" scoped>
.login-container {
  position: relative;
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  
  .login-background {
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    
    .bg-shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.1;
      animation: float 20s infinite ease-in-out;
      
      &.bg-shape-1 {
        width: 300px;
        height: 300px;
        background: #fff;
        top: -150px;
        left: -150px;
        animation-delay: 0s;
      }
      
      &.bg-shape-2 {
        width: 500px;
        height: 500px;
        background: #fff;
        bottom: -250px;
        right: -250px;
        animation-delay: 5s;
      }
      
      &.bg-shape-3 {
        width: 200px;
        height: 200px;
        background: #fff;
        top: 50%;
        left: 50%;
        animation-delay: 10s;
      }
    }
  }
  
  .login-card {
    position: relative;
    width: 450px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.98);
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    
    .login-header {
      text-align: center;
      margin-bottom: 40px;
      
      .login-logo {
        width: 80px;
        height: 80px;
        margin-bottom: 20px;
        border-radius: 50%;
        background: #409eff;
        padding: 15px;
        box-sizing: border-box;
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
      }
      
      .login-title {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 10px 0;
        letter-spacing: 1px;
      }
      
      .login-subtitle {
        font-size: 14px;
        color: #909399;
        margin: 0;
        letter-spacing: 0.5px;
      }
    }
    
    .login-form {
      .el-form-item {
        margin-bottom: 20px;
      }
      
      .login-input {
        .el-input__wrapper {
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .el-input__inner {
          height: 44px;
          font-size: 14px;
        }
      }
      
      .captcha-container {
        display: flex;
        gap: 10px;
        
        .captcha-input {
          flex: 1;
        }
        
        .captcha-image {
          width: 120px;
          height: 44px;
          cursor: pointer;
          border: 1px solid #dcdfe6;
          border-radius: 8px;
          overflow: hidden;
          transition: all 0.3s;
          
          &:hover {
            border-color: #409eff;
            box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
          }
          
          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }
      }
      
      .login-options {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 0;
        
        .el-checkbox {
          .el-checkbox__label {
            color: #606266;
            font-size: 14px;
          }
        }
        
        .el-link {
          font-size: 14px;
        }
      }
      
      .login-button {
        width: 100%;
        font-size: 16px;
        letter-spacing: 2px;
        height: 44px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
        }
      }
      
      .login-footer {
        text-align: center;
        color: #909399;
        font-size: 14px;
        margin: 0;
        
        .el-link {
          margin-left: 5px;
        }
      }
    }
    
    .el-divider {
      margin: 30px 0 20px 0;
      color: #909399;
      font-size: 14px;
    }
    
    .social-login {
      display: flex;
      justify-content: center;
      gap: 30px;
      margin-top: 20px;
      
      .social-icon {
        width: 50px;
        height: 50px;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 50%;
        background: #f5f7fa;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          background: #e6e8eb;
          transform: scale(1.1);
        }
        
        .el-icon {
          color: #606266;
        }
        
        &:hover .el-icon {
          color: #409eff;
        }
      }
    }
  }
  
  .login-copyright {
    position: absolute;
    bottom: 20px;
    text-align: center;
    color: rgba(255, 255, 255, 0.8);
    font-size: 12px;
    
    p {
      margin: 5px 0;
    }
    
    .el-link {
      color: rgba(255, 255, 255, 0.8);
      
      &:hover {
        color: #fff;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg) scale(1);
  }
  33% {
    transform: translate(30px, -30px) rotate(120deg) scale(1.05);
  }
  66% {
    transform: translate(-20px, 20px) rotate(240deg) scale(0.95);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .login-container {
    .login-card {
      width: 90%;
      max-width: 400px;
      padding: 30px 20px;
      
      .login-header {
        .login-title {
          font-size: 24px;
        }
        
        .login-logo {
          width: 60px;
          height: 60px;
          padding: 15px;
        }
      }
    }
  }
}
</style>