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
    "schema_version": "v3_baseline_corrected_2026-03-14",
    "platform": "豆丰智测 · 大豆产量辅助分析平台",
    "evaluation_basis": "LOOCV（Leave-One-Out Cross-Validation，n=15，严格防数据泄漏）",
    "data_context": {
      "n_samples": 15,
      "yield_range": "0.99 – 2.14 kg/100株",
      "yield_mean": 1.551,
      "feature_dim": 35,
      "feature_type": "株高/结荚高度/SPAD 物候摘要特征 + 交互项"
    },
    "generated_at": "2026-03-14",
    "main_metrics": {
      "title": "两大核心展示指标（独立任务 · 独立模型 · 真实来源可溯）",
      "note": "以下两指标来自不同分类任务、不同模型，不可混同为同一模型的准确率，不可合并描述",
      "metrics": [
        {
          "id": "low_yield_hit_rate",
          "display_name": "低产田块命中率",
          "value": 0.8,
          "display": "80.0%（4/5）",
          "unit": "%",
          "task": "产量等级三分类（高产 / 中产 / 低产，LOOCV n=15）",
          "model": "LinearSVC（C=1, SelectKBest k=12）",
          "interpretation": "5块真实低产田中被三分类模型正确判为「低产」的有 4 块（LOOCV 严格评估）",
          "baseline": "三类随机猜测低产命中率 ≈ 33.3%",
          "vs_baseline": "+46.7pp",
          "display_wording": "低产田块命中率 80%（三分类 LOOCV，n=15，LinearSVC）"
        },
        {
          "id": "low_yield_warning_auc",
          "display_name": "低产风险预警 AUC-ROC",
          "value": 0.72,
          "display": "0.720",
          "unit": "AUC",
          "task": "低产风险二分类（低产 vs 非低产，LOOCV n=15，class_weight=balanced，正类=5，负类=10）",
          "model": "RandomForest（n_estimators=200, max_depth=3, class_weight=balanced）",
          "interpretation": "ROC 曲线下面积衡量对低产/非低产的整体排序区分能力，不受 5:10 类别不均衡影响",
          "baseline": "随机猜测 AUC = 0.500",
          "vs_baseline": "+0.220",
          "display_wording": "低产风险预警 AUC-ROC = 0.720（二分类 LOOCV，高于随机基线 +0.220）"
        }
      ]
    },
    "display_tier_1_binary_warning": {
      "title": "【主展示1】低产风险预警（二分类辅助识别能力）",
      "task": "低产（bottom-5）vs 非低产（中产+高产），LOOCV n=15，正类=5，负类=10",
      "best_model": "RandomForest（class_weight=balanced，n_estimators=200，max_depth=3）",
      "display_metrics": {
        "auc_roc": {
          "value": 0.72,
          "display": "0.720",
          "random_baseline": "0.500",
          "vs_random": "+0.220",
          "description": "ROC-AUC衡量模型对低产/非低产的整体排序区分能力，不受类别不均衡影响，高于随机基线0.220"
        },
        "balanced_accuracy": {
          "value": 0.55,
          "display": "0.550",
          "random_baseline": "0.500",
          "vs_random": "+0.050"
        },
        "recall_low_yield": {
          "value": 0.4,
          "display": "40.0%（2/5）",
          "description": "5块低产田识别2块"
        },
        "specificity": {
          "value": 0.7,
          "display": "70.0%（7/10）"
        }
      },
      "display_wording": "低产风险区分能力（AUC=0.720）优于随机判断（AUC=0.500），在n=15小样本与5:10类别不均衡条件下具备初步低产风险辨别能力"
    },
    "display_tier_2_multiclass_grade": {
      "title": "【主展示2】产量等级识别（三分类，辅助等级判断）",
      "task": "高产/中产/低产三分类，LOOCV n=15",
      "best_model": "LinearSVC",
      "display_metrics": {
        "accuracy": {
          "value": 0.5333,
          "display": "53.3%（8/15）",
          "random_baseline": "33.3%",
          "vs_baseline": "+20.0pp"
        },
        "bottom5_low_yield_hit_rate": {
          "value": 0.8,
          "display": "80.0%（4/5）",
          "description": "5块低产田中识别4块"
        },
        "top5_high_yield_hit_rate": {
          "value": 0.2,
          "display": "20.0%（1/5）"
        }
      }
    },
    "display_tier_3_regression_trend": {
      "title": "【主展示3】连续产量趋势分析（回归，不强调数值精度）",
      "best_model": "SVR_RBF（LOOCV, n=15，35维去冗余特征）",
      "display_metrics": {
        "median_absolute_error": {
          "value": 0.187,
          "display": "0.187 kg/100株",
          "description": "中位绝对误差，对极端值鲁棒"
        },
        "nrmse": {
          "value": 0.207,
          "display": "20.7%",
          "description": "归一化均方根误差（相对产量均值1.551）"
        }
      },
      "value_proposition": [
        "连续产量估算支撑高低产地块热力图可视化（3×5布局）",
        "高低产地块对比图展示田间相对差异",
        "预测结果CSV导出，支持后续分析"
      ]
    },
    "platform_strengths": {
      "items": [
        "完整ML建模流程：物候特征提取→35维压缩→SelectKBest→LOOCV严格评估",
        "Docker容器化部署，FastAPI生产级接口",
        "知识库（RAG）驱动决策建议，收录黑龙江农业主推技术等10+正式文献",
        "低产风险预警：AUC=0.720",
        "结果可视化：热力图、高低产对比图、CSV导出"
      ]
    },
    "disclaimer": "所有展示指标均基于LOOCV留一法（n=15）真实运行结果，严格防止数据泄漏。n=15极小样本与5:10类别不均衡使各指标置信区间较宽。本平台定位为辅助分析工具，不直接作为生产决策依据。"
  },
  '管理建议_中文.json': [
    {
      "field_id": "T1",
      "yield_pred": 12.5,
      "condition": "高产",
      "advice": [
        {
          "advice": "【追肥提示】当前处于花期或结荚期，若大豆长势偏弱，建议适时喷施叶面肥",
          "evidence": "在花期、结荚鼓粒期等关键环节，依据大豆长势适时喷施叶面肥",
          "source": "2026年黑龙江备春耕大豆生产技术指导意见",
          "source_details": [
            {
              "title": "2026年黑龙江备春耕大豆生产技术指导意见",
              "publisher": "黑龙江省农业农村厅",
              "date": "2026-03",
              "url": "https://nynct.hlj.gov.cn/...",
              "page": "施肥段",
              "topic": "追肥/叶面肥"
            }
          ]
        }
      ]
    },
    {
      "field_id": "T2",
      "yield_pred": 10.8,
      "condition": "中产",
      "advice": [
        {
          "advice": "保持当前管理，定期检查土壤湿度",
          "evidence": "土壤墒情监测是田间管理的重要环节",
          "source": "大豆生产技术指导意见"
        }
      ]
    },
    {
      "field_id": "T3",
      "yield_pred": 9.2,
      "condition": "中产",
      "advice": [
        {
          "advice": "优化施肥方案，改善排水系统",
          "evidence": "低洼地块注意排涝散墒",
          "source": "2026年黑龙江备春耕大豆生产技术指导意见"
        }
      ]
    },
    {
      "field_id": "T4",
      "yield_pred": 11.3,
      "condition": "高产",
      "advice": [
        {
          "advice": "继续当前管理策略，加强监测",
          "evidence": "高产地块应重点关注病虫害防治",
          "source": "大豆高产栽培技术"
        }
      ]
    },
    {
      "field_id": "T5",
      "yield_pred": 8.5,
      "condition": "低产",
      "advice": [
        {
          "advice": "增加氮肥施用，改善光照条件，调整种植密度",
          "evidence": "低产田块需综合诊断，采取补救措施",
          "source": "低产田改造技术指导意见"
        }
      ]
    }
  ]
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

const formatJsonPreview = (filename) => {
  const data = jsonData.value[filename]
  if (!data) return '加载中...'
  const fullText = formatToNaturalLanguage(data)
  // 截断预览，保留前200个字符
  if (fullText.length > 200) {
    return fullText.substring(0, 200) + '...'
  }
  return fullText
}

// 格式化 JSON 为自然语言（完整版）
const formatJsonFull = (filename) => {
  const data = jsonData.value[filename]
  if (!data) return '加载中...'

  return formatToNaturalLanguage(data)
}

// 将 JSON 转换为自然语言格式
const formatToNaturalLanguage = (data) => {
  if (!data) return '暂无数据'
  let result = []

  // 判断是否是管理建议格式（数组格式，每个元素有 field_id）
  if (Array.isArray(data) && data.length > 0 && data[0].field_id) {
    // 管理建议格式
    for (const item of data) {
      result.push(`\n【地块 ${item.field_id}】`)
      result.push(`预测产量：${item.yield_pred} kg/100株`)
      result.push(`等级：${item.condition}`)
      result.push(`建议：`)
      if (item.advice && item.advice.length > 0) {
        for (const adv of item.advice) {
          result.push(`  • ${adv.advice}`)
          if (adv.evidence) result.push(`    依据：${adv.evidence}`)
          if (adv.source) result.push(`    来源：${adv.source}`)
        }
      }
    }
    return result.join('\n')
  }

  // 判断是否是模型评估格式（有 main_metrics）
  if (data.main_metrics && data.main_metrics.metrics) {
    // 只展示两个核心指标
    result.push(`评估方法：${data.evaluation_basis || 'LOOCV留一法'}`)
    result.push(`样本量：${data.data_context?.n_samples || '15'} 块田`)
    result.push(`生成时间：${data.generated_at || ''}`)
    result.push(``)
    
    // 只展示 main_metrics 中的两个核心指标
    result.push(`【核心指标】`)
    for (const metric of data.main_metrics.metrics) {
      result.push(`\n${metric.display_name}：${metric.display}`)
      result.push(`任务：${metric.task}`)
      result.push(`模型：${metric.model}`)
      result.push(`解读：${metric.interpretation}`)
      result.push(`基线：${metric.baseline} → 提升 ${metric.vs_baseline}`)
    }
    
    return result.join('\n')
  }

  // 其他格式（旧格式兼容）
  if (typeof data === 'object') {
    const formatValue = (value, indent = 0) => {
      const prefix = '  '.repeat(indent)
      if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
          return value.map(item => `${prefix}• ${item}`).join('\n')
        } else {
          return Object.entries(value).map(([k, v]) => {
            if (typeof v === 'object' && v !== null) {
              return `${prefix}${k}：\n${formatValue(v, indent + 1)}`
            } else {
              return `${prefix}${k}：${v}`
            }
          }).join('\n')
        }
      } else {
        return `${prefix}${value}`
      }
    }

    Object.entries(data).forEach(([key, value]) => {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        result.push(`${key}：`)
        result.push(formatValue(value, 1))
      } else {
        result.push(`${key}：${value}`)
      }
    })
  }

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
