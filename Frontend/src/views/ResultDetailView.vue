<template>
  <div class="detail-view-page">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="logo">
        <img src="/vite.png" alt="Logo" class="logo-image" />
        <div class="logo-text">
          <div class="logo-title">豆丰智测</div>
          <div class="logo-subtitle">大豆估产与决策平台</div>
        </div>
      </div>
      <button class="nav-button" @click="goToUpload">即刻估产</button>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="page-title">
        <h1>分析结果详情</h1>
        <p class="subtitle">任务编号：{{ runId }}</p>
      </div>

      <!-- 结果展示区域 -->
      <div class="results-container">
        <!-- 图片区块 1: 热力图 -->
        <div class="result-card image-card">
          <div class="card-header">
            <h3>热力图</h3>
            <button class="btn-download" @click="downloadFile('热力图_中文绿色_3x5.png')">
              下载
            </button>
          </div>
          <div class="image-preview" @click="openImageModal('热力图_中文绿色_3x5.png')">
            <img
              :src="getImageUrl('热力图_中文绿色_3x5.png')"
              alt="热力图"
              class="thumbnail"
            />
          </div>
        </div>

        <!-- 图片区块 2: 高低产对比图 -->
        <div class="result-card image-card">
          <div class="card-header">
            <h3>高低产对比图</h3>
            <button class="btn-download" @click="downloadFile('高低产对比图_中文绿色.png')">
              下载
            </button>
          </div>
          <div class="image-preview" @click="openImageModal('高低产对比图_中文绿色.png')">
            <img
              :src="getImageUrl('高低产对比图_中文绿色.png')"
              alt="高低产对比图"
              class="thumbnail"
            />
          </div>
        </div>

        <!-- JSON 区块 1: 模型评估 -->
        <div class="result-card json-card">
          <div class="card-header">
            <h3>模型评估</h3>
            <button class="btn-download" @click="downloadFile('模型评估_中文.json')">
              下载
            </button>
          </div>
          <div class="json-preview" @click="openJsonModal('模型评估_中文.json')">
            <div class="natural-language-preview">
              {{ formatJsonPreview('模型评估_中文.json') }}
            </div>
          </div>
        </div>

        <!-- JSON 区块 2: 管理建议 -->
        <div class="result-card json-card">
          <div class="card-header">
            <h3>管理建议</h3>
            <button class="btn-download" @click="downloadFile('管理建议_中文.json')">
              下载
            </button>
          </div>
          <div class="json-preview half-preview" @click="openJsonModal('管理建议_中文.json')">
            <div class="natural-language-preview">
              {{ formatJsonPreview('管理建议_中文.json') }}
            </div>
            <div class="fade-overlay"></div>
          </div>
        </div>

        <!-- CSV 区块: 预测结果 -->
        <div class="result-card csv-card">
          <div class="card-header">
            <h3>预测结果</h3>
            <button class="btn-download" @click="downloadFile('预测结果_中文.csv')">
              下载
            </button>
          </div>
          <div class="csv-info">
            <p>CSV 数据文件，点击下载按钮查看完整数据</p>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-section">
        <button class="back-button" @click="goBack">返回</button>
      </div>
    </main>

    <!-- 图片预览弹窗 -->
    <div v-if="imageModalVisible" class="modal-overlay" @click="closeImageModal">
      <div class="modal-content image-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ currentImageName }}</h3>
          <div class="modal-actions">
            <button class="btn-modal" @click="downloadFile(currentImageName)">下载</button>
            <button class="btn-close" @click="closeImageModal">×</button>
          </div>
        </div>
        <div class="modal-body">
          <img :src="getImageUrl(currentImageName)" alt="预览图" class="full-image" />
        </div>
      </div>
    </div>

    <!-- JSON 详情弹窗 -->
    <div v-if="jsonModalVisible" class="modal-overlay" @click="closeJsonModal">
      <div class="modal-content json-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ currentJsonName }}</h3>
          <div class="modal-actions">
            <button class="btn-modal" @click="copyJsonContent">复制</button>
            <button class="btn-close" @click="closeJsonModal">×</button>
          </div>
        </div>
        <div class="modal-tabs">
          <button
            :class="['tab-button', { active: jsonViewMode === 'natural' }]"
            @click="jsonViewMode = 'natural'"
          >
            自然语言
          </button>
          <button
            :class="['tab-button', { active: jsonViewMode === 'json' }]"
            @click="jsonViewMode = 'json'"
          >
            JSON
          </button>
        </div>
        <div class="modal-body scrollable">
          <div v-if="jsonViewMode === 'natural'" class="natural-language-full">
            {{ formatJsonFull(currentJsonName) }}
          </div>
          <pre v-else class="json-raw">{{ getJsonRaw(currentJsonName) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 获取 runId
const runId = ref(route.params.runId)

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 模拟 JSON 数据（实际应该从 API 获取）
const jsonData = ref({
  '模型评估_中文.json': {
    "平均绝对误差MAE": 0.3282558928070673,
    "均方根误差RMSE": 0.41309998174300216,
    "决定系数R2": -0.8212636538589277,
    "模型权重": {
      "随机森林": 0.5423017665029983,
      "极端随机树": 0.45769823349700156
    }
  },
  '管理建议_中文.json': {
    "T1": {
      "预测产量(kg/100株)": 12.5,
      "等级": "高产",
      "建议": ["增加灌溉频率", "适当施肥", "注意病虫害防治"]
    },
    "T2": {
      "预测产量(kg/100株)": 10.8,
      "等级": "中产",
      "建议": ["保持当前管理", "定期检查土壤湿度"]
    },
    "T3": {
      "预测产量(kg/100株)": 9.2,
      "等级": "中产",
      "建议": ["优化施肥方案", "改善排水系统"]
    },
    "T4": {
      "预测产量(kg/100株)": 11.3,
      "等级": "高产",
      "建议": ["继续当前管理策略", "加强监测"]
    },
    "T5": {
      "预测产量(kg/100株)": 8.5,
      "等级": "低产",
      "建议": ["增加氮肥施用", "改善光照条件", "调整种植密度"]
    }
  }
})

// 图片弹窗状态
const imageModalVisible = ref(false)
const currentImageName = ref('')

// JSON 弹窗状态
const jsonModalVisible = ref(false)
const currentJsonName = ref('')
const jsonViewMode = ref('natural') // 'natural' 或 'json'

// 获取图片 URL
const getImageUrl = (filename) => {
  return `${API_BASE_URL}/result/${runId.value}/${encodeURIComponent(filename)}`
}

// 打开图片弹窗
const openImageModal = (filename) => {
  currentImageName.value = filename
  imageModalVisible.value = true
}

// 关闭图片弹窗
const closeImageModal = () => {
  imageModalVisible.value = false
}

// 打开 JSON 弹窗
const openJsonModal = (filename) => {
  currentJsonName.value = filename
  jsonViewMode.value = 'natural'
  jsonModalVisible.value = true
}

// 关闭 JSON 弹窗
const closeJsonModal = () => {
  jsonModalVisible.value = false
}

// 格式化 JSON 为自然语言（预览版，截断）
const formatJsonPreview = (filename) => {
  const data = jsonData.value[filename]
  if (!data) return '加载中...'

  return formatToNaturalLanguage(data)
}

// 格式化 JSON 为自然语言（完整版）
const formatJsonFull = (filename) => {
  const data = jsonData.value[filename]
  if (!data) return '加载中...'

  return formatToNaturalLanguage(data)
}

// 将 JSON 转换为自然语言格式
const formatToNaturalLanguage = (data) => {
  let result = []

  const formatValue = (value, indent = 0) => {
    const prefix = '  '.repeat(indent)

    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value)) {
        return value.map(item => `${prefix}• ${item}`).join('\n')
      } else {
        const entries = Object.entries(value)
        return entries.map(([k, v]) => {
          if (typeof v === 'object' && v !== null) {
            return `${prefix}${k}：\n${formatValue(v, indent + 1)}`
          } else {
            const formattedV = typeof v === 'number' ? v.toFixed(4) : v
            return `${prefix}${k}：${formattedV}`
          }
        }).join('\n')
      }
    } else {
      const formattedValue = typeof value === 'number' ? value.toFixed(4) : value
      return `${prefix}${formattedValue}`
    }
  }

  Object.entries(data).forEach(([key, value]) => {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      result.push(`${key}：`)
      result.push(formatValue(value, 1))
    } else {
      const formattedValue = typeof value === 'number' ? value.toFixed(4) : value
      result.push(`${key}：${formattedValue}`)
    }
  })

  return result.join('\n')
}

// 获取原始 JSON
const getJsonRaw = (filename) => {
  const data = jsonData.value[filename]
  return JSON.stringify(data, null, 2)
}

// 复制 JSON 内容
const copyJsonContent = () => {
  let content = ''
  if (jsonViewMode.value === 'natural') {
    content = formatJsonFull(currentJsonName.value)
  } else {
    content = getJsonRaw(currentJsonName.value)
  }

  navigator.clipboard.writeText(content).then(() => {
    alert('已复制到剪贴板')
  })
}

// 下载文件
const downloadFile = (filename) => {
  const encodedFilename = encodeURIComponent(filename)
  const downloadUrl = `${API_BASE_URL}/result/${runId.value}/${encodedFilename}`

  // 创建 <a> 标签并触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 跳转到上传页面
const goToUpload = () => {
  router.push('/upload')
}

onMounted(() => {
  // 可以在这里添加从 API 加载 JSON 数据的逻辑
})
</script>

<style scoped>
/* 配色方案 */
.detail-view-page {
  min-height: 100vh;
  background: #f5f5f0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: #1a1510;
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
  background: #eab308;
  color: #1a1510;
  border: none;
  border-radius: 24px;
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
  max-width: 1200px;
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
  color: #2a2520;
  font-weight: 700;
}

.subtitle {
  font-size: 16px;
  color: #666;
}

/* 结果展示区域 */
.results-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.result-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
}

.result-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 20px;
  color: #2a2520;
  font-weight: 600;
  margin: 0;
}

.btn-download {
  padding: 8px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-download:hover {
  background: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

/* 图片卡片 */
.image-preview {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: #f9f9f9;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.thumbnail {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  transition: transform 0.3s;
}

.image-preview:hover .thumbnail {
  transform: scale(1.05);
}

/* JSON 卡片 */
.json-preview {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  max-height: 200px;
  overflow: hidden;
}

.json-preview:hover {
  background: #f0f0f0;
}

.json-preview.half-preview {
  max-height: 150px;
}

.natural-language-preview {
  white-space: pre-wrap;
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.fade-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(to bottom, transparent, #f9f9f9);
  pointer-events: none;
}

/* CSV 卡片 */
.csv-info {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.csv-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* 操作按钮 */
.action-section {
  text-align: center;
  margin-top: 40px;
}

.back-button {
  padding: 12px 40px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.back-button:hover {
  background: #5a6268;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 90%;
  max-height: 90%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.image-modal {
  max-width: 1000px;
}

.json-modal {
  max-width: 800px;
  width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #2a2520;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-modal {
  padding: 6px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-modal:hover {
  background: #45a049;
}

.btn-close {
  width: 32px;
  height: 32px;
  background: #f0f0f0;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  color: #666;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s;
}

.btn-close:hover {
  background: #e0e0e0;
  color: #333;
}

.modal-tabs {
  display: flex;
  padding: 0 24px;
  border-bottom: 1px solid #e0e0e0;
  background: #f9f9f9;
}

.tab-button {
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  transition: all 0.3s;
}

.tab-button.active {
  color: #4CAF50;
  border-bottom-color: #4CAF50;
}

.tab-button:hover {
  color: #4CAF50;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-body.scrollable {
  max-height: 500px;
}

.full-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}

.natural-language-full {
  white-space: pre-wrap;
  font-family: 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.json-raw {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  overflow-x: auto;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1100px) {
  .results-container {
    grid-template-columns: 1fr;
  }
}
</style>
