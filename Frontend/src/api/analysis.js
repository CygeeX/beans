// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 训练模型
 * @param {FormData} formData - 包含 ground, yield_xlsx, layout 的表单数据
 * @returns {Promise} 返回训练结果
 */
export async function trainModel(formData) {
  // 设置25分钟超时（1500秒）
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 1500000); // 1500秒 = 25分钟
  
  try {
    const response = await fetch(`/api/train`, {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }));
      throw new Error(error.detail || `HTTP错误: ${response.status}`);
    }

    const result = await response.json();

    console.log('[analysis api] trainModel 收到响应')
    console.log('[analysis api] result =', result)
    console.log('[analysis api] result.summary =', result.summary)
    console.log('[analysis api] result.outputs =', result.outputs)
    console.log('[analysis api] result.files =', result.files)

    // 保存到历史记录
    const historyPayload = {
      runId: result.run_id,
      type: 'train',
      time: new Date().toLocaleString('zh-CN'),
      status: 'completed',
      // 注意：后端返回的是 outputs，不是 files
      files: result.outputs || result.files || [
        { name: '训练结果报告.xlsx', filename: 'train_result.xlsx' },
        { name: '模型参数.csv', filename: 'model_params.csv' }
      ],
      summary: result.summary || null
    }

    console.log('[analysis api] 准备保存历史记录')
    console.log('[analysis api] historyPayload.summary =', historyPayload.summary)

    saveToHistory(historyPayload);

    console.log('[analysis api] 历史记录已保存')

    return result;
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      console.error('训练超时：25分钟仍未完成');
      throw new Error('训练时间过长（超过25分钟），建议使用历史记录查看或联系管理员');
    }
    
    console.error('训练模型失败:', error);
    throw error;
  }
}

/**
 * 预测产量
 * @param {FormData} formData - 包含 ground, layout 的表单数据
 * @returns {Promise} 返回预测结果
 */
export async function predictYield(formData) {
  try {
    const response = await fetch(`/api/predict`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '预测失败')
    }

    const result = await response.json()

    console.log('[analysis api] predictYield 收到响应')
    console.log('[analysis api] result =', result)
    console.log('[analysis api] result.summary =', result.summary)
    console.log('[analysis api] result.outputs =', result.outputs)
    console.log('[analysis api] result.files =', result.files)

    // 保存到历史记录
    const historyPayload = {
      runId: result.run_id,
      type: 'predict',
      time: new Date().toLocaleString('zh-CN'),
      status: 'completed',
      // 注意：后端返回的是 outputs，不是 files
      files: result.outputs || result.files || [
        { name: '预测结果报告.xlsx', filename: 'predict_result.xlsx' },
        { name: '详细分析数据.csv', filename: 'analysis_data.csv' }
      ],
      summary: result.summary || null
    }

    console.log('[analysis api] 准备保存历史记录')
    console.log('[analysis api] historyPayload.summary =', historyPayload.summary)

    saveToHistory(historyPayload)

    console.log('[analysis api] 历史记录已保存')

    return result
  } catch (error) {
    console.error('预测产量失败:', error)
    throw error
  }
}

/**
 * 下载结果文件
 * @param {string} runId - 任务ID
 * @param {string} filename - 文件名
 */
export async function downloadResult(runId, filename) {
  try {
    const response = await fetch(`${API_BASE_URL}/result/${runId}/${filename}`)

    if (!response.ok) {
      throw new Error('文件下载失败')
    }

    // 创建下载链接
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载文件失败:', error)
    throw error
  }
}

/**
 * 保存分析记录到本地存储
 * @param {Object} record - 分析记录
 */
function saveToHistory(record) {
  console.log('[history] saveToHistory 被调用')
  console.log('[history] record =', record)
  console.log('[history] record.summary =', record.summary)

  const history = JSON.parse(localStorage.getItem('analysisHistory') || '[]')
  console.log('[history] 当前历史记录数量 =', history.length)

  history.unshift(record)

  // 只保留最近 20 条记录
  if (history.length > 20) {
    history.splice(20)
  }

  localStorage.setItem('analysisHistory', JSON.stringify(history))
  console.log('[history] 历史记录已保存到 localStorage')
  console.log('[history] 新的历史记录数量 =', history.length)

  // 验证保存是否成功
  const saved = JSON.parse(localStorage.getItem('analysisHistory') || '[]')
  console.log('[history] 验证: 最新记录的 summary =', saved[0]?.summary)
}

/**
 * 健康检查
 * @returns {Promise} 返回健康状态
 */
export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    return await response.json()
  } catch (error) {
    console.error('健康检查失败:', error)
    throw error
  }
}
