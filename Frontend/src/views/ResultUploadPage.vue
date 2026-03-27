<template>
  <div class="upload-page">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="logo">
        <img src="/vite.png" alt="Logo" class="logo-image" />
        <div class="logo-text">
          <div class="logo-title">豆丰智测</div>
          <div class="logo-subtitle">大豆估产与决策平台</div>
        </div>
      </div>
      <button class="nav-button" @click="goToResult">地块管理分析</button>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="page-title">
        <h1>即刻估产</h1>
        <p class="subtitle">上传观测数据，智能预测大豆产量</p>
      </div>

      <!-- 分析类型选择 -->
      <div class="analysis-type">
        <label class="radio-label">
          <input type="radio" v-model="analysisType" value="predict" />
          <span>快速预测（仅需观测数据）</span>
        </label>
        <label class="radio-label">
          <input type="radio" v-model="analysisType" value="train" />
          <span>训练模型（需观测数据+产量记录）</span>
        </label>
      </div>

      <!-- 文件上传区域 -->
      <div class="upload-section">
        <!-- 地面观测数据包 -->
        <FileUpload
          label="上传地面观测数据包"
          required
          accept=".zip"
          hint="包含多次观测记录的压缩包"
          v-model="files.ground"
        />

        <!-- 真实产量记录表（仅训练模式） -->
        <FileUpload
          v-if="analysisType === 'train'"
          label="上传真实产量记录表"
          required
          accept=".xlsx,.xls"
          hint="包含15块田实际产量的Excel表"
          v-model="files.yieldXlsx"
        />

        <!-- 布局文件（可选） -->
        <FileUpload
          label="上传布局文件（可选）"
          accept=".csv"
          hint="布局配置文件"
          v-model="files.layout"
        />
      </div>

      <!-- 操作按钮 -->
      <div class="action-section">
        <button
          class="submit-button"
          :disabled="!canSubmit || isProcessing"
          @click="handleSubmit"
        >
          <l-dot-stream
            v-if="isProcessing"
            size="60"
            speed="2.5"
            color="white"
          ></l-dot-stream>
          <span v-else>开始分析</span>
        </button>
      </div>

      <!-- 状态提示 -->
      <div v-if="status.message" class="status-message" :class="status.type">
        <div class="status-icon">
          <l-bouncy
            v-if="status.type === 'loading'"
            size="40"
            speed="1.75"
            color="#eab308"
          ></l-bouncy>
          <span v-else-if="status.type === 'success'">✅</span>
          <span v-else-if="status.type === 'error'">❌</span>
        </div>
        <div class="status-text">{{ status.message }}</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import FileUpload from '@/components/FileUpload.vue'
import { trainModel, predictYield } from '@/api/analysis'
import { dotStream, bouncy } from 'ldrs'

dotStream.register()
bouncy.register()

const router = useRouter()

// 分析类型
const analysisType = ref('predict')

// 文件数据
const files = ref({
  ground: null,
  yieldXlsx: null,
  layout: null
})

// 处理状态
const isProcessing = ref(false)
const status = ref({
  type: '',
  message: ''
})

// 是否可以提交
const canSubmit = computed(() => {
  if (analysisType.value === 'predict') {
    return files.value.ground !== null
  } else {
    return files.value.ground !== null && files.value.yieldXlsx !== null
  }
})

// 跳转到结果页面
const goToResult = () => {
  router.push('/result')
}

// 提交分析
const handleSubmit = async () => {
  isProcessing.value = true
  status.value = { type: 'loading', message: '正在上传文件...' }

  try {
    const formData = new FormData()
    formData.append('ground', files.value.ground)

    if (analysisType.value === 'train' && files.value.yieldXlsx) {
      formData.append('yield_xlsx', files.value.yieldXlsx)
    }

    if (files.value.layout) {
      formData.append('layout', files.value.layout)
    }

    status.value = { type: 'loading', message: '预计10min-20min左右分析完毕，请等待...' }

    let response
    if (analysisType.value === 'predict') {
      response = await predictYield(formData)
    } else {
      response = await trainModel(formData)
    }

    status.value = { type: 'success', message: '分析完成！正在跳转...' }

    // 跳转到结果详情页
    setTimeout(() => {
      router.push(`/result/${response.run_id}`)
    }, 1000)

  } catch (error) {
    status.value = {
      type: 'error',
      message: error.message || '分析失败，请检查文件格式后重试'
    }
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
/* 配色方案 - 参考截图 */
.upload-page {
  min-height: 100vh;
  background: #f5f5f0; /* 浅米白背景 */
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: #1a1510; /* 深棕黑背景 */
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-image {
  height: 40px;
  width: auto;
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-title {
  font-size: 20px;
  font-weight: bold;
  background: linear-gradient(to right, rgb(227, 224, 186), rgb(181, 153, 78));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-subtitle {
  font-size: 12px;
  color: white;
  font-weight: 400;
}

.nav-button {
  padding: 10px 24px;
  background: #eab308; /* 暖黄色 */
  color: #1a1510; /* 深色文字 */
  border: none;
  border-radius: 24px; /* 圆角 */
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.nav-button:hover {
  background: #d9a307;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(234, 179, 8, 0.3);
}

.main-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 20px;
}

.page-title {
  text-align: center;
  margin-bottom: 50px;
}

.page-title h1 {
  font-size: 36px;
  margin-bottom: 12px;
  color: #2a2520; /* 深灰色 */
  font-weight: 700;
}

.subtitle {
  font-size: 16px;
  color: #666; /* 中灰色 */
}

.analysis-type {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 30px;
  display: flex;
  gap: 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 15px;
  color: #333; /* 深灰文字 */
}

.radio-label input {
  margin-right: 10px;
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #4CAF50; /* 豆绿色 */
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 40px;
}

.action-section {
  text-align: center;
}

.submit-button {
  padding: 14px 56px;
  background: #4CAF50; /* 豆绿色 */
  color: white;
  border: none;
  border-radius: 28px; /* 圆角 */
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-button:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.submit-button:disabled {
  background: #d0d0d0; /* 浅灰色 */
  cursor: not-allowed;
  box-shadow: none;
}

.status-message {
  margin-top: 30px;
  padding: 20px 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 15px;
  animation: fadeIn 0.3s;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.status-message.loading {
  border-left: 4px solid #eab308; /* 暖黄色 */
}

.status-message.success {
  border-left: 4px solid #4CAF50; /* 豆绿色 */
}

.status-message.error {
  border-left: 4px solid #dc3545; /* 低饱和红色 */
}

.status-icon {
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 45px;
}

.status-text {
  font-size: 15px;
  font-weight: 500;
  color: #333; /* 深灰色 */
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
