<template>
  <div class="result-page">
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
        <h1>地块管理分析</h1>
        <p class="subtitle">查看历史分析记录和详细结果</p>
      </div>

      <!-- 历史记录列表 -->
      <div class="history-section">
        <h2>历史记录</h2>
        <div v-if="history.length === 0" class="empty-state">
          <p>暂无分析记录</p>
          <button class="primary-button" @click="goToUpload">开始第一次分析</button>
        </div>
        <div v-else class="history-list">
          <div
            v-for="record in history"
            :key="record.runId"
            class="history-item"
            :class="{ active: currentRunId === record.runId }"
            @click="selectRecord(record.runId)"
          >
            <div class="record-icon">📊</div>
            <div class="record-info">
              <div class="record-time">{{ record.time }}</div>
              <div class="record-meta">
                <span class="record-type">{{ record.type === 'predict' ? '快速预测' : '训练模型' }}</span>
                <span class="record-status" :class="record.status">
                  {{ record.status === 'completed' ? '已完成' : '处理中' }}
                </span>
              </div>
            </div>
            <div class="record-actions">
              <button class="action-btn" @click.stop="viewDetail(record.runId)">查看详情</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 当前查看的结果详情 -->
      <div v-if="currentResult" class="result-detail">
        <h2>最新分析结果详情</h2>
        <div class="detail-card">
          <div class="detail-header">
            <h3>{{ currentResult.time }} 分析结果</h3>
          </div>

          <div class="detail-info">
            <div class="info-row">
              <span class="info-label">任务编号：</span>
              <span class="info-value">{{ currentResult.runId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">分析类型：</span>
              <span class="info-value">{{ currentResult.type === 'predict' ? '快速预测' : '训练模型' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">完成时间：</span>
              <span class="info-value">{{ currentResult.time }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">状态：</span>
              <span class="info-value status-badge">✅ 已完成</span>
            </div>
          </div>

          <!-- 预测结果摘要 -->
          <div v-if="currentResult.summary" class="result-summary">
            <h4>预测结果摘要</h4>
            <div class="summary-grid">
              <div class="summary-item">
                <div class="summary-label">平均预测产量</div>
                <div class="summary-value">{{ formatYield(currentResult.summary.avgYield) }} {{ currentResult.summary.unit || 'kg/100株' }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">最高产量地块</div>
                <div class="summary-value">{{ currentResult.summary.maxBlock }} ({{ formatYield(currentResult.summary.maxYield) }} {{ currentResult.summary.unit || 'kg/100株' }})</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">最低产量地块</div>
                <div class="summary-value">{{ currentResult.summary.minBlock }} ({{ formatYield(currentResult.summary.minYield) }} {{ currentResult.summary.unit || 'kg/100株' }})</div>
              </div>
            </div>
          </div>
          <div v-else class="result-summary">
            <h4>预测结果摘要</h4>
            <p class="no-summary">暂无摘要数据</p>
          </div>

          <!-- 可下载文件
          <div class="download-section">
            <h4>可下载文件</h4>
            <div class="file-list">
              <div
                v-for="file in currentResult.files"
                :key="file.name"
                class="file-item"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.name }}</span>
                <button class="download-btn" @click="downloadFile(file)">下载</button>
              </div>
            </div>
          </div> -->

          <!-- 操作按钮 -->
          <div class="detail-actions">
            <button class="secondary-button" @click="goToUpload">重新分析</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { downloadResult } from '@/api/analysis'

const router = useRouter()
const route = useRoute()

// 历史记录
const history = ref([])

// 当前查看的 runId
const currentRunId = ref(null)

// 当前结果详情
const currentResult = computed(() => {
  console.log('[detail page] currentResult computed 被调用')
  console.log('[detail page] currentRunId.value =', currentRunId.value)

  if (!currentRunId.value) {
    console.log('[detail page] currentRunId 为空，返回 null')
    return null
  }

  const result = history.value.find(r => r.runId === currentRunId.value)
  console.log('[detail page] 找到的 result =', result)
  console.log('[detail page] result?.summary =', result?.summary)

  return result
})

// 加载历史记录
const loadHistory = () => {
  console.log('[detail page] loadHistory 被调用')

  const stored = localStorage.getItem('analysisHistory')
  console.log('[detail page] localStorage 中的原始数据长度 =', stored?.length || 0)

  if (stored) {
    history.value = JSON.parse(stored)
    console.log('[detail page] 历史记录数量 =', history.value.length)

    // 打印前3条记录的 summary
    history.value.slice(0, 3).forEach((record, index) => {
      console.log(`[detail page] 记录 ${index}: runId =`, record.runId)
      console.log(`[detail page] 记录 ${index}: summary =`, record.summary)
    })
  } else {
    console.log('[detail page] localStorage 中没有历史记录')
  }

  // 如果 URL 中有 runId，则显示该记录
  if (route.params.runId) {
    currentRunId.value = route.params.runId
    console.log('[detail page] URL 中的 runId =', currentRunId.value)
  } else if (history.value.length > 0) {
    currentRunId.value = history.value[0].runId
    console.log('[detail page] 使用最新记录的 runId =', currentRunId.value)
  }

  console.log('[detail page] 当前选中的 runId =', currentRunId.value)
}

// 选择记录
const selectRecord = (runId) => {
  currentRunId.value = runId
  router.push(`/result/${runId}`)
}

// 查看详情
const viewDetail = (runId) => {
  selectRecord(runId)
}

// 下载文件
const downloadFile = async (file) => {
  try {
    await downloadResult(currentRunId.value, file.filename)
  } catch (error) {
    alert('下载失败：' + error.message)
  }
}

// 跳转到上传页面
const goToUpload = () => {
  router.push('/upload')
}

// 格式化产量数值（保持原始精度，不强制小数位数）
const formatYield = (value) => {
  console.log('[summary render] formatYield 被调用, value =', value)
  if (value === null || value === undefined) return '-'
  // 直接返回数值，让浏览器自然显示，不强制 toFixed
  return Number(value)
}

// 监控 currentResult 的变化
watch(currentResult, (newVal) => {
  console.log('[summary render] currentResult 变化')
  console.log('[summary render] currentResult =', newVal)
  console.log('[summary render] currentResult?.summary =', newVal?.summary)

  if (newVal?.summary) {
    console.log('[summary render] summary 存在:')
    console.log('[summary render]   avgYield =', newVal.summary.avgYield)
    console.log('[summary render]   maxBlock =', newVal.summary.maxBlock)
    console.log('[summary render]   maxYield =', newVal.summary.maxYield)
    console.log('[summary render]   minBlock =', newVal.summary.minBlock)
    console.log('[summary render]   minYield =', newVal.summary.minYield)
    console.log('[summary render]   unit =', newVal.summary.unit)
  } else {
    console.log('[summary render] summary 不存在或为空')
  }
}, { immediate: true })

onMounted(() => {
  console.log('[detail page] onMounted 被调用')
  loadHistory()
})
</script>

<style scoped>
/* 配色方案 - 参考截图 */
.result-page {
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
  color: #2a2520; /* 深灰色 */
  font-weight: 700;
}

.subtitle {
  font-size: 16px;
  color: #666; /* 中灰色 */
}

.history-section {
  background: white;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.history-section h2 {
  font-size: 22px;
  margin-bottom: 24px;
  color: #2a2520; /* 深灰色 */
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999; /* 浅灰色 */
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fafafa; /* 非常浅的灰色 */
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.history-item:hover {
  background: #f5f5f5;
}

.history-item.active {
  border-color: #4CAF50; /* 豆绿色 */
  background: #f9fdf9; /* 非常浅的绿色 */
}

.record-icon {
  font-size: 32px;
  margin-right: 16px;
}

.record-info {
  flex: 1;
}

.record-time {
  font-size: 16px;
  font-weight: 600;
  color: #333; /* 深灰色 */
  margin-bottom: 6px;
}

.record-meta {
  display: flex;
  gap: 12px;
  font-size: 14px;
}

.record-type {
  color: #666; /* 中灰色 */
}

.record-status {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.record-status.completed {
  background: #e8f5e9; /* 浅绿背景 */
  color: #2e7d32; /* 深绿文字 */
}

.record-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  padding: 8px 18px;
  background: #4CAF50; /* 豆绿色 */
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #45a049;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.result-detail {
  background: white;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.result-detail h2 {
  font-size: 22px;
  margin-bottom: 24px;
  color: #2a2520; /* 深灰色 */
  font-weight: 600;
}

.detail-card {
  background: #fafafa; /* 非常浅的灰色 */
  padding: 28px;
  border-radius: 10px;
}

.detail-header h3 {
  font-size: 20px;
  color: #333; /* 深灰色 */
  margin-bottom: 24px;
  font-weight: 600;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 28px;
}

.info-row {
  display: flex;
  font-size: 15px;
}

.info-label {
  font-weight: 600;
  color: #666; /* 中灰色 */
  min-width: 100px;
}

.info-value {
  color: #333; /* 深灰色 */
}

.status-badge {
  padding: 4px 12px;
  background: #e8f5e9; /* 浅绿背景 */
  color: #2e7d32; /* 深绿文字 */
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.result-summary {
  margin-bottom: 28px;
  padding: 24px;
  background: white;
  border-radius: 10px;
}

.result-summary h4 {
  font-size: 18px;
  margin-bottom: 18px;
  color: #333; /* 深灰色 */
  font-weight: 600;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-item {
  padding: 18px;
  background: #f9fdf9; /* 非常浅的绿色 */
  border-radius: 8px;
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: #666; /* 中灰色 */
  margin-bottom: 10px;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: #4CAF50; /* 豆绿色 */
}

.no-summary {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 20px;
}

.download-section {
  margin-bottom: 28px;
}

.download-section h4 {
  font-size: 18px;
  margin-bottom: 18px;
  color: #333; /* 深灰色 */
  font-weight: 600;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  gap: 14px;
}

.file-icon {
  font-size: 24px;
}

.file-name {
  flex: 1;
  font-size: 15px;
  color: #333; /* 深灰色 */
}

.download-btn {
  padding: 8px 20px;
  background: #4CAF50; /* 豆绿色 */
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.download-btn:hover {
  background: #45a049;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.detail-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.primary-button,
.secondary-button {
  padding: 12px 32px;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.primary-button {
  background: #4CAF50; /* 豆绿色 */
  color: white;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
}

.primary-button:hover {
  background: #45a049;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.secondary-button {
  background: #6c757d; /* 中灰色 */
  color: white;
}

.secondary-button:hover {
  background: #5a6268;
}
</style>
