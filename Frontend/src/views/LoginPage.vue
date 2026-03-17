<template>
  <div class="login-page">
    <!-- 左上角 Logo -->
    <div class="logo-container">
      <div class="flex items-center space-x-3">
        <img src="/vite.png" alt="Logo" class="h-10 w-auto" />
        <div class="flex flex-col">
          <span class="text-xl font-bold bg-gradient-to-r from-[rgb(227,224,186)] to-[rgb(181,153,78)] bg-clip-text text-transparent">豆丰智测</span>
          <span class="text-xs text-white tracking-wider">大豆估产与决策平台</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="login-container">
      <!-- 左侧：登录表单 -->
      <div class="login-form-section">
        <div class="form-wrapper">
          <h1 class="form-title">大豆估产与决策平台</h1>
          <p class="form-subtitle">欢迎登录</p>

          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label for="username" class="form-label">账号</label>
              <input
                id="username"
                v-model="loginForm.username"
                type="text"
                class="form-input"
                placeholder="请输入账号"
                required
              />
            </div>

            <div class="form-group">
              <label for="password" class="form-label">密码</label>
              <input
                id="password"
                v-model="loginForm.password"
                type="password"
                class="form-input"
                placeholder="请输入密码"
                required
              />
            </div>

            <div class="form-options">
              <label class="checkbox-label">
                <input
                  v-model="loginForm.remember"
                  type="checkbox"
                  class="checkbox-input"
                />
                <span>记住我</span>
              </label>
              <a href="#" class="forgot-link">忘记密码？</a>
            </div>

            <button type="submit" class="submit-button">
              登录
            </button>

            <div v-if="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>
          </form>

          <div class="form-footer">
            <p>还没有账号？ <a href="#" class="register-link">立即注册</a></p>
          </div>
        </div>
      </div>

      <!-- 右侧：装饰图片 -->
      <div class="illustration-section">
        <div class="illustration-content">
          <div class="illustration-circle"></div>
          <div class="illustration-text">
            <h2>智能估产</h2>
            <p>基于Docker架构的大豆估产与决策平台</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const loginForm = ref({
  username: '',
  password: '',
  remember: false
})

const errorMessage = ref('')

const handleLogin = () => {
  // 验证账号密码
  if (loginForm.value.username === 'admin' && loginForm.value.password === 'admin') {
    // 登录成功，跳转到主页
    router.push('/')
  } else {
    // 登录失败，显示错误信息
    errorMessage.value = '账号或密码错误，请重试'
    setTimeout(() => {
      errorMessage.value = ''
    }, 3000)
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #1a1510;
  position: relative;
  overflow: hidden;
}

.logo-container {
  position: absolute;
  top: 30px;
  left: 40px;
  z-index: 10;
}

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 左侧表单区域 */
.login-form-section {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 40px;
  max-width: 600px;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

.form-title {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(to right, rgb(227, 224, 186), rgb(181, 153, 78));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.form-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 40px;
}

.login-form {
  width: 100%;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  transition: all 0.3s;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.form-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.15);
  border-color: #eab308;
  box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.1);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #eab308;
}

.forgot-link {
  font-size: 14px;
  color: #eab308;
  text-decoration: none;
  transition: color 0.3s;
}

.forgot-link:hover {
  color: #d9a307;
}

.submit-button {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  background: #eab308;
  color: #1a1510;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-button:hover {
  background: #d9a307;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(234, 179, 8, 0.4);
}

.submit-button:active {
  transform: translateY(0);
}

.error-message {
  margin-top: 16px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: #fca5a5;
  font-size: 14px;
  text-align: center;
}

.form-footer {
  margin-top: 32px;
  text-align: center;
}

.form-footer p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.register-link {
  color: #eab308;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.register-link:hover {
  color: #d9a307;
}

/* 右侧装饰区域 */
.illustration-section {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 40px;
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.1) 0%, rgba(181, 153, 78, 0.1) 100%);
  position: relative;
}

.illustration-content {
  position: relative;
  width: 100%;
  max-width: 500px;
  height: 500px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.illustration-circle {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.2) 0%, rgba(181, 153, 78, 0.2) 100%);
  border: 2px solid rgba(234, 179, 8, 0.3);
  position: absolute;
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.5;
  }
}

.illustration-text {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 40px;
}

.illustration-text h2 {
  font-size: 48px;
  font-weight: 700;
  background: linear-gradient(to right, rgb(227, 224, 186), rgb(181, 153, 78));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}

.illustration-text p {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-container {
    flex-direction: column;
  }

  .illustration-section {
    display: none;
  }

  .login-form-section {
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .logo-container {
    top: 20px;
    left: 20px;
  }

  .login-form-section {
    padding: 40px 20px;
  }

  .form-title {
    font-size: 24px;
  }

  .illustration-text h2 {
    font-size: 36px;
  }
}
</style>
