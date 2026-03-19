<template>
  <div class="auth-page">

    <!-- ── 顶部导航栏 ── -->
    <nav class="topnav">
      <div class="nav-logo">
        <img src="/vite.png" alt="Logo" class="nav-logo-img" />
        <div class="nav-logo-text">
          <span class="nav-brand">豆丰智测</span>
          <span class="nav-sub">大豆估产与决策平台</span>
        </div>
      </div>
      <span class="nav-hint">智能估产 · 精准决策</span>
    </nav>

    <!-- ── 主体内容 ── -->
    <div class="auth-body">

      <!-- 左侧：表单区域 -->
      <div class="form-panel">
        <div class="card">
          <div class="card-header">
            <h1 class="card-title">登录</h1>
            <p class="card-subtitle">登录豆丰智测</p>
          </div>

          <form @submit.prevent="handleLogin">
            <div class="field">
              <label class="label">用户名</label>
              <input
                v-model="form.username"
                type="text"
                class="input"
                placeholder="请输入用户名"
                autocomplete="username"
                required
              />
            </div>

            <div class="field">
              <label class="label">密码</label>
              <input
                v-model="form.password"
                type="password"
                class="input"
                placeholder="请输入密码"
                autocomplete="current-password"
                required
              />
            </div>

            <div v-if="error" class="error-tip">{{ error }}</div>

            <button type="submit" class="btn-submit">登录</button>
          </form>

          <p class="switch-tip">
            还没有账号？
            <router-link to="/register" class="switch-link">立即注册</router-link>
          </p>
        </div>
      </div>

      <!-- 右侧：波浪动画区域 -->
      <div class="visual-panel">
        <WaveCanvas class="wave-fill" />
        <div class="visual-overlay">
          <p class="visual-tagline">产量估算 · 决策支持</p>
          <p class="visual-desc">基于Docker架构的大豆估产与决策平台</p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { loginApi } from '@/api/user'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import WaveCanvas from '@/components/WaveCanvas.vue'

const router = useRouter()
const form = ref({ username: '', password: '' })
const error = ref('')

const handleLogin = async () => {
  try {
    const response = await loginApi({
      username: form.value.username,
      password: form.value.password
    })
    console.log('登录成功:', response.data)
    error.value = ''
    alert('登录成功！')
    router.push('/home')
  } catch (err) {
    console.error('登录失败:', err)
    const errorMsg = err.response?.data?.detail || '登录失败，请重试'
    error.value = errorMsg
    setTimeout(() => { error.value = '' }, 3000)
  }
}
</script>

<style scoped>
/* ══════════════════════════════════════
   色彩 Token
══════════════════════════════════════ */
.auth-page {
  /* 背景 */
  --bg:            #261608;
  --bg-noise:      rgba(80, 45, 10, 0.35);

  /* 导航 */
  --nav-bg:        rgba(12, 6, 1, 0.45);
  --nav-border:    rgba(200, 160, 100, 0.1);

  /* 毛玻璃卡片 */
  --card-bg:       rgba(195, 148, 82, 0.1);
  --card-border:   rgba(220, 182, 125, 0.18);
  --card-hi:       rgba(240, 208, 155, 0.18);   /* 顶部高光 */
  --card-shadow:   0 24px 64px rgba(0, 0, 0, 0.5), 0 4px 16px rgba(0, 0, 0, 0.3);

  /* 文字 */
  --text-title:    #f0e4c8;
  --text-sub:      rgba(215, 182, 132, 0.6);
  --text-label:    rgba(228, 198, 152, 0.82);
  --text-muted:    rgba(195, 158, 105, 0.65);

  /* 输入框 */
  --input-bg:      rgba(255, 238, 205, 0.06);
  --input-border:  rgba(200, 162, 105, 0.22);
  --input-focus:   rgba(200, 162, 105, 0.58);
  --input-glow:    rgba(180, 138, 72, 0.16);
  --input-text:    #f0e4c8;
  --input-ph:      rgba(195, 158, 105, 0.45);

  /* 按钮 */
  --btn-bg:        #c49a5a;
  --btn-hover:     #d4aa6a;
  --btn-text:      #1a0e04;

  /* 链接 */
  --link:          rgba(200, 162, 105, 0.82);
  --link-hover:    #c49a5a;

  /* 错误 */
  --err-bg:        rgba(160, 48, 28, 0.12);
  --err-border:    rgba(160, 48, 28, 0.3);
  --err-text:      #d4806a;
}

/* ══════════════════════════════════════
   页面基础
══════════════════════════════════════ */
.auth-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  /* 统一深棕背景 + 微妙径向光晕，给 backdrop-filter 提供层次 */
  background:
    radial-gradient(ellipse 70% 60% at 25% 55%, var(--bg-noise) 0%, transparent 65%),
    radial-gradient(ellipse 50% 40% at 75% 25%, rgba(55, 30, 5, 0.3) 0%, transparent 55%),
    var(--bg);
  font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  color: var(--text-title);
}

/* ══════════════════════════════════════
   顶部导航栏
══════════════════════════════════════ */
.topnav {
  flex-shrink: 0;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  background: var(--nav-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--nav-border);
  position: relative;
  z-index: 10;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-logo-img {
  height: 32px;
  width: auto;
}

.nav-logo-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-brand {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(to right, rgb(227, 224, 186), rgb(181, 153, 78));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.nav-sub {
  font-size: 10px;
  color: rgba(200, 162, 105, 0.5);
  letter-spacing: 0.05em;
}

.nav-hint {
  font-size: 12px;
  color: rgba(200, 162, 105, 0.4);
  letter-spacing: 0.08em;
  font-weight: 300;
}

/* ══════════════════════════════════════
   主体布局
══════════════════════════════════════ */
.auth-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* ── 左侧表单面板 ── */
.form-panel {
  flex: 0 0 30%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 48px 40px;
}

/* ══════════════════════════════════════
   毛玻璃卡片
══════════════════════════════════════ */
.card {
  width: 100%;
  max-width: 372px;
  background: var(--card-bg);
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  border: 1px solid var(--card-border);
  border-radius: 18px;
  padding: 44px 40px 38px;
  box-shadow: var(--card-shadow), inset 0 1px 0 var(--card-hi);
}

.card-header {
  margin-bottom: 30px;
}

.card-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 6px;
  letter-spacing: -0.01em;
}

.card-subtitle {
  font-size: 12.5px;
  color: var(--text-sub);
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.01em;
}

/* ══════════════════════════════════════
   表单字段
══════════════════════════════════════ */
.field {
  margin-bottom: 20px;
}

.label {
  display: block;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--text-label);
  margin-bottom: 7px;
  letter-spacing: 0.01em;
}

.input {
  width: 100%;
  padding: 11px 14px;
  font-size: 14px;
  font-family: inherit;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 9px;
  color: var(--input-text);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
  box-sizing: border-box;
  /* 阻止浏览器默认 color-scheme 影响 */
  color-scheme: dark;
}

.input::placeholder {
  color: var(--input-ph);
}

.input:focus {
  border-color: var(--input-focus);
  background: rgba(255, 238, 205, 0.09);
  box-shadow: 0 0 0 3px var(--input-glow);
}

/* 覆盖浏览器自动填充蓝色背景 */
.input:-webkit-autofill,
.input:-webkit-autofill:hover,
.input:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0 1000px #2e1c0a inset;
  -webkit-text-fill-color: var(--input-text);
  caret-color: var(--input-text);
  transition: background-color 5000s ease-in-out 0s;
}

/* 错误提示 */
.error-tip {
  margin-bottom: 16px;
  padding: 10px 14px;
  background: var(--err-bg);
  border: 1px solid var(--err-border);
  border-radius: 8px;
  color: var(--err-text);
  font-size: 13px;
}

/* ══════════════════════════════════════
   提交按钮
══════════════════════════════════════ */
.btn-submit {
  width: 100%;
  padding: 13px;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  background: var(--btn-bg);
  color: var(--btn-text);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  letter-spacing: 0.06em;
  transition: background 0.2s, transform 0.15s, box-shadow 0.2s;
  margin-top: 6px;
}

.btn-submit:hover {
  background: var(--btn-hover);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(180, 138, 72, 0.3);
}

.btn-submit:active {
  transform: translateY(0);
  box-shadow: none;
}

/* ── 底部切换 ── */
.switch-tip {
  margin-top: 22px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}

.switch-link {
  color: var(--link);
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s;
}

.switch-link:hover {
  color: var(--link-hover);
}

/* ══════════════════════════════════════
   右侧视觉面板
══════════════════════════════════════ */
.visual-panel {
  flex: 1;
  position: relative;
  background: transparent;
  overflow: hidden;
}

.wave-fill {
  position: absolute;
  inset: 0;
}

.wave-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.visual-overlay {
  position: absolute;
  bottom: 56px;
  left: 0;
  right: 0;
  text-align: center;
  pointer-events: none;
}

.visual-tagline {
  font-size: 20px;
  font-weight: 500;
  color: rgba(230, 200, 150, 0.55);
  margin: 0 0 8px;
  letter-spacing: 0.1em;
}

.visual-desc {
  font-size: 12px;
  color: rgba(200, 162, 105, 0.3);
  margin: 0;
  letter-spacing: 0.04em;
}

/* ══════════════════════════════════════
   响应式
══════════════════════════════════════ */
@media (max-width: 900px) {
  .form-panel { flex: 0 0 54%; }
}

@media (max-width: 680px) {
  .auth-body { flex-direction: column; }

  .form-panel {
    flex: none;
    width: 100%;
    padding: 40px 24px 48px;
  }

  .visual-panel {
    flex: none;
    height: 160px;
    order: -1;
  }

  .visual-overlay {
    bottom: auto;
    top: 50%;
    transform: translateY(-50%);
  }

  .visual-tagline { font-size: 15px; }
  .visual-desc { display: none; }

  .topnav { padding: 0 20px; }
  .nav-hint { display: none; }

  .card {
    padding: 36px 26px 30px;
    max-width: 100%;
  }
}
</style>
